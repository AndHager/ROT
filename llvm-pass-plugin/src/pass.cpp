#include "llvm/IR/CFG.h"
#include "llvm/IR/PassManager.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/CodeGen/MachineFunction.h"

#include <iostream>
#include <mgclient.h>

using namespace llvm;
using namespace std;

#define DEBUG false

#define PRINT_IR false
#define PURGE_DB false

namespace
{

    struct CDFGPass : public PassInfoMixin<CDFGPass>
    {
        string get_bb_name(BasicBlock *bb)
        {
            string str;
            raw_string_ostream OS(str);
            bb->printAsOperand(OS, false);
            return OS.str();
        }

        template <typename LLVM_Type>
        string llvm_to_string(LLVM_Type *obj)
        {
            string str;
            raw_string_ostream OS(str);
            OS << *obj << "\n";
            return OS.str();
        }

        mg_session *connect_to_db(const char *host, uint16_t port)
        {
            mg_init();
#if DEBUG
            printf("mgclient version: %s\n", mg_client_version());
#endif

            mg_session_params *params = mg_session_params_make();
            if (!params)
            {
                fprintf(stderr, "failed to allocate session parameters\n");
                exit(1);
            }
            mg_session_params_set_host(params, host);
            mg_session_params_set_port(params, port);
            mg_session_params_set_sslmode(params, MG_SSLMODE_DISABLE);

            mg_session *session = NULL;
            int status = mg_connect(params, &session);
            mg_session_params_destroy(params);
            if (status < 0)
            {
                printf("failed to connect to Memgraph: %s\n", mg_session_error(session));
                mg_session_destroy(session);
                exit(1);
            }
            return session;
        }

        void disconnect(mg_session *session)
        {
            mg_session_destroy(session);
            mg_finalize();
        }

        void exec_qeury(mg_session *session, const char *query)
        {
            if (mg_session_run(session, query, NULL, NULL, NULL, NULL) < 0)
            {
                outs() << "failed to execute query: " << query << " mg error: " << mg_session_error(session) << "\n";
                mg_session_destroy(session);
                exit(1);
            }
            if (mg_session_pull(session, NULL))
            {
                outs() << "failed to pull results of the query: " << mg_session_error(session) << "\n";
                mg_session_destroy(session);
                exit(1);
            }

            int status = 0;
            mg_result *result;
            int rows = 0;
            while ((status = mg_session_fetch(session, &result)) == 1)
            {
                rows++;
            }

            if (status < 0)
            {
                outs() << "error occurred during query execution: " << mg_session_error(session) << "\n";
            }
            else
            {
#if DEBUG
                printf("query executed successfuly and returned %d rows\n", rows);
#endif
            }
        }

        void create_mod(mg_session *session, string module_name)
        {
            string store_mod = "MERGE (mod {name: '" + module_name + "', kind: 'module'})";
            string qry = store_mod + '\n';
            exec_qeury(session, qry.c_str());
        }

        void create_func(mg_session *session, string f_name, string module_name)
        {
            string store_func = "MERGE (func {module_name: '" + module_name + "', name: '" + f_name + "', kind: 'function'})";
            string qry = store_func + '\n';
            exec_qeury(session, qry.c_str());
        }

        void connect_mod_func(mg_session *session, string f_name, string module_name)
        {
            string match_mod = "MATCH (mod {name: '" + module_name + "', kind: 'module'})";
            string match_func = "MATCH (func {module_name: '" + module_name + "', name: '" + f_name + "', kind: 'function'})";
            string rel = " MERGE (mod)-[:MOD]->(func);";
            string qry = match_mod + '\n' + match_func + '\n' + rel + '\n';
            exec_qeury(session, qry.c_str());
        }

        void create_bb(mg_session *session, BasicBlock *bb, string f_name, string module_name)
        {
            string store_bb = "MERGE (bb {module_name: '" + module_name + "', func_name: '" + f_name + "', name: '" + get_bb_name(bb) + "', kind: 'basicblock'})";
            string set_bb_code = " SET bb.code =  '" + sanitize_str(llvm_to_string(bb)) + "'";
            string qry = store_bb + '\n' + set_bb_code + '\n';
            exec_qeury(session, qry.c_str());
        }

        void connect_bbs(mg_session *session, BasicBlock *first_bb, BasicBlock *second_bb, string f_name, string module_name)
        {
            // MERGE: create if not exist else match
            string match_first = "MATCH (first_bb {module_name: '" + module_name + "', func_name: '" + f_name + "', name: '" + get_bb_name(first_bb) + "', kind: 'basicblock'})";
            string match_second = "MATCH (second_bb {module_name: '" + module_name + "', func_name: '" + f_name + "', name: '" + get_bb_name(second_bb) + "', kind: 'basicblock'})";
            string rel = " MERGE (first_bb)-[:CFG]->(second_bb);";
            string qry = match_first + '\n' + match_second + rel + '\n';
            exec_qeury(session, qry.c_str());
        }

        void connect_func_bb(mg_session *session, BasicBlock *bb, string f_name, string module_name)
        {
            // MERGE: create if not exist else match
            string match_bb = "MATCH (bb {module_name: '" + module_name + "', func_name: '" + f_name + "', name: '" + get_bb_name(bb) + "', kind: 'basicblock'})";
            string match_func = "MATCH (func {module_name: '" + module_name + "', name: '" + f_name + "', kind: 'function'})";
            string rel = " MERGE (func)-[:FUNC]->(bb);";
            string qry = match_bb + '\n' + match_func + '\n' + rel + '\n';
            exec_qeury(session, qry.c_str());
        }

        string sanitize_str(string str) {
            const string illegal_chars = "\n\"\\\'\t()[]{}~";
            for (char c : illegal_chars) {
                replace(str.begin(), str.end(), c, '_');
            }
            return str;
        }

        void create_inst(mg_session *session, string code, string op_name, string f_name, string module_name)
        {
            code = sanitize_str(code);

            string store_inst = "MERGE (inst {module_name: '" + module_name + "', func_name: '" + f_name + "', name: '" + op_name + "', inst: '" + code + "', kind: 'instruction'})";
            string qry = store_inst + '\n';
            exec_qeury(session, qry.c_str());
        }

        void create_label(mg_session *session, string code, string label_name, string f_name, string module_name)
        {
            // MERGE: create if not exist else match
            code = sanitize_str(code);

            string store_inst = "MERGE (label {module_name: '" + module_name + "', func_name: '" + f_name + "', name: '" + label_name + "', code: '" + code + "', kind: 'label'})";
            string qry = store_inst + '\n';
            exec_qeury(session, qry.c_str());
        }

        void connect_label_inst(mg_session *session, string label_code, string label_name, string code, string op_name, string f_name, string module_name)
        {
            label_code = sanitize_str(label_code);
            code = sanitize_str(code);

            string match_label = "MATCH (label {module_name: '" + module_name + "', func_name: '" + f_name + "', name: '" + label_name + "', code: '" + label_code + "', kind: 'label'})";
            string match_inst = "MATCH (inst {module_name: '" + module_name + "', func_name: '" + f_name + "', name: '" + op_name + "', inst: '" + code + "', kind: 'instruction'})";
            string rel = "MERGE (label)-[:LABEL]->(inst);";
            string qry = match_label + '\n' + match_inst + '\n' + rel + '\n';
            exec_qeury(session, qry.c_str());
        }

        void connect_bb_inst(mg_session *session, BasicBlock *bb, string code, string op_name, string f_name, string module_name)
        {
            // MERGE: create if not exist else match
            code = sanitize_str(code);

            string match_bb = "MATCH (bb {module_name: '" + module_name + "', func_name: '" + f_name + "', name: '" + get_bb_name(bb) + "', kind: 'basicblock'})";
            string match_inst = "MATCH (inst {module_name: '" + module_name + "', func_name: '" + f_name + "', name: '" + op_name + "', inst: '" + code + "', kind: 'instruction'})";
            string rel = "MERGE (bb)-[:ENTRY]->(inst);";
            string qry = match_bb + '\n' + match_inst + '\n' + rel + '\n';
            exec_qeury(session, qry.c_str());
        }


        void connect_insts(mg_session *session, string src_str, string src_op_name, string dst_str, string dst_op_name, string f_name, string module_name)
        {
            // MERGE: create if not exist else match
            src_str = sanitize_str(src_str);
            dst_str = sanitize_str(dst_str);

            string match_src = "MATCH (src_inst {module_name: '" + module_name + "', func_name: '" + f_name + "', name: '" + src_op_name + "', inst: '" + src_str + "', kind: 'instruction'})";
            string match_dst = "MATCH (dst_inst {module_name: '" + module_name + "', func_name: '" + f_name + "', name: '" + dst_op_name + "', inst: '" + dst_str + "', kind: 'instruction'})";
            string rel = "MERGE (src_inst)-[:DFG]->(dst_inst);";
            string qry = match_src + '\n' + match_dst + '\n' + rel + '\n';
            exec_qeury(session, qry.c_str());
        }

        void connect_inst_inst_chain(mg_session *session, string src_str, string src_op_name, string dst_str, string dst_op_name, string f_name, string module_name)
        {
            // MERGE: create if not exist else match
            src_str = sanitize_str(src_str);
            dst_str = sanitize_str(dst_str);

            string match_src = "MATCH (src_inst {module_name: '" + module_name + "', func_name: '" + f_name + "', name: '" + src_op_name + "', inst: '" + src_str + "'})";
            string match_dst = "MATCH (dst_inst {module_name: '" + module_name + "', func_name: '" + f_name + "', name: '" + dst_op_name + "', inst: '" + dst_str + "'})";
            string rel = "MERGE (src_inst)-[:CHAIN]->(dst_inst);";
            string qry = match_src + '\n' + match_dst + '\n' + rel + '\n';
            exec_qeury(session, qry.c_str());
        }

        PreservedAnalyses run(Module &M, ModuleAnalysisManager &MAM)
        {
#if DEBUG
            outs() << "Running CDFGPass\n";
#endif
            mg_session *session = connect_to_db("localhost", 7687);

#if PURGE_DB
            // Clear database
            auto del = "MATCH (n) DETACH DELETE n;";
            exec_qeury(session, del);
#endif

            string index = "CREATE INDEX ON :bb;\n";
            exec_qeury(session, index.c_str());
            index = "CREATE INDEX ON :label;\n";
            exec_qeury(session, index.c_str());
            index = "CREATE INDEX ON :inst;";
            exec_qeury(session, index.c_str());


            // Push CDFG to DB
            string module_name = M.getName().str();
            create_mod(session, module_name);
#if PRINT_IR
            outs() << "Module Name: " << module_name << "\n";
#endif
            for (Function &F : M)
            {
                string f_name = F.getName().str();
                create_func(session, f_name, module_name);
                connect_mod_func(session, f_name, module_name);
#if PRINT_IR
                outs() << " Function: " << f_name << "\n";
#endif
                for (BasicBlock &bb : F)
                {
                    string bb_name = get_bb_name(&bb);
                    create_bb(session, &bb, f_name, module_name);
                    connect_func_bb(session, &bb, f_name, module_name);
#if PRINT_IR
                    outs() << "  Label: " << bb_name << "\n";
#endif
                    for (BasicBlock *suc_bb : successors(&bb))
                    {
                        create_bb(session, suc_bb, f_name, module_name);
                        connect_bbs(session, &bb, suc_bb, f_name, module_name);
                    }

                    bool entry = true;
                    Instruction* prev = NULL;
                    for (Instruction &inst : bb)
                    {
                        string inst_str = llvm_to_string(&inst);
                        string op_name = inst.getOpcodeName();
#if PRINT_IR
                        outs() << "   " << inst_str;
#endif
                        create_inst(session, inst_str, op_name, f_name, module_name);
                        if (entry) {
                            connect_bb_inst(session, &bb, inst_str, op_name, f_name, module_name);
                            entry = false;
                        } else {
                            string src_str = llvm_to_string(prev);
                            string src_op_name = prev->getOpcodeName();
                            connect_inst_inst_chain(session, src_str, src_op_name, inst_str, op_name, f_name, module_name);
                        }
                        prev = &inst;

                        Instruction::op_iterator opEnd = inst.op_end();
                        for (Instruction::op_iterator opi = inst.op_begin(); opi != opEnd; opi++)
                        {
                            // TODO: create_op
                            // TODO: connect_op_inst

                            Value *op = opi->get();
                            Type *tp = op->getType();
                            if (!tp->isLabelTy())
                            {
                                string src_str = llvm_to_string(op);
                                string src_op_name = "Const";

                                Instruction *src_inst = dyn_cast<Instruction>(op);
                                if (src_inst) {
                                    // TODO: connect_inst_op
                                    src_op_name = src_inst->getOpcodeName();
                                } else { // Const

                                }
#if DEBUG
                                outs() << "    - " << src_str;
#endif
                                connect_insts(session, src_str, src_op_name, inst_str, op_name, f_name, module_name);
                            } else {
                                string code = llvm_to_string(op);
                                string label_name = "?Label?";
                                create_label(session, code, label_name, f_name, module_name);
                                connect_label_inst(session, code, label_name, inst_str, op_name, f_name, module_name);
                            }
                        }
                        // connect_bb_inst(session, &bb, &inst, f_name, module_name);
                    }
                }
            }

            disconnect(session);

            return PreservedAnalyses::all();
        }
    };

} // end anonymous namespace

PassPluginLibraryInfo getPassPluginInfo() {
  const auto callback = [](PassBuilder &PB) {
    PB.registerOptimizerLastEPCallback(
        [](ModulePassManager &MPM, OptimizationLevel Level) {
          MPM.addPass(CDFGPass());
        });
    PB.registerPipelineParsingCallback(
        [](StringRef Name, ModulePassManager &MPM,
           ArrayRef<PassBuilder::PipelineElement>) {
          if (Name == "cdfg") {
            MPM.addPass(CDFGPass());
            return true;
          }
          return false;
        });
  };
  return {LLVM_PLUGIN_API_VERSION, "name", "0.0.1", callback};
};

extern "C" LLVM_ATTRIBUTE_WEAK PassPluginLibraryInfo llvmGetPassPluginInfo()
{
    return getPassPluginInfo();
}

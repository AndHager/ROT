from model import instruction_model, program

ignore_underscore = True
fuctions_to_ignore = [
    'exit', 'register_fini', 'frame_dummy', 
    'stdio_exit_handler', 'cleanup_stdio', 'global_stdio_init.part.0'
]


def filter_functions(source_line, last_function_is_ignored) -> bool:
    elems = source_line.split(' ')
    elen = len(elems)
    
    if elen == 2:
        function_name_unstripped = elems[1]
        if function_name_unstripped[-2:] == '>:':
            is_underscore_fn = ignore_underscore and function_name_unstripped[1] == '_'
            stripped_function_name = function_name_unstripped[1:-2]
            is_ign_fn = stripped_function_name in fuctions_to_ignore
            last_function_is_ignored = is_underscore_fn or is_ign_fn
    
    return last_function_is_ignored


def parse_file(fqfn, parse_line, ignore) -> program.Program:
    instructions = []
    with open(fqfn, 'r', errors='replace') as file:
            lines = file.read().split('\n')
            last_function_is_ignored = False
            for source_line in lines:
                filered = filter_functions(source_line, last_function_is_ignored)
                last_function_is_ignored = filered
                if not filered:
                    # print("Parsing line: ", source_line.strip())
                    inst = parse_line(source_line, ignore)
                    if inst != None:
                        instructions.append(inst)
            
    return program.Program(instructions)


def parse_address_cnt(fqfn, addr_inst_map, addr_getter):
    op_inst_cnt_map = {}
    with open(fqfn, 'r', errors='replace') as file:
            lines = file.read().split('\n')
            for source_line in lines:
                inst_addr = addr_getter(source_line)
                if inst_addr & 0x80000000 == 0:
                    if inst_addr in addr_inst_map:
                        cnt = 1
                        if inst_addr in op_inst_cnt_map:
                            cnt += op_inst_cnt_map[inst_addr][1]
                            
                        op_inst_cnt_map[inst_addr] = (addr_inst_map[inst_addr], cnt)
            
    return op_inst_cnt_map

def parse_val_cnt(fqfn, val_getter, ignore, static_file, count):
    val = 0
    with open(fqfn, 'r', errors='replace') as file:
            lines = file.read().split('\n')
            if static_file:
                last_function_is_ignored = False
                for source_line in lines:
                    filered = filter_functions(source_line, last_function_is_ignored)
                    last_function_is_ignored = filered
                    if not filered:
                        val += val_getter(source_line, ignore, count)
            else:
                val = sum([
                    val_getter(source_line, ignore, count)
                    for source_line in lines
                ])
            
    return val

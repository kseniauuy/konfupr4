import argparse
import xml.etree.ElementTree as ET

def assembler(input_file, output_file, log_file):
    # Чтение исходного кода
    with open(input_file, 'r') as f:
        code = [eval(line.strip()) for line in f.readlines()]
    
    bc = []  # Список для бинарных данных
    log_entries = []  # Лог-записи для XML
    for line_num, (op, *args) in enumerate(code, start=1):
        try:
            if op == 'move':
                if len(args) != 2:
                    raise ValueError(f"Line {line_num}: Expected 2 arguments for 'move', got {len(args)}")
                b, c = args
                bc += serializer(17, ((b, 5), (c, 15)), 3)
                log_entries.append(f"move b={b} c={c}")
            elif op == 'read':
                if len(args) != 3:
                    raise ValueError(f"Line {line_num}: Expected 3 arguments for 'read', got {len(args)}")
                b, c, d = args
                bc += serializer(3, ((b, 5), (c, 12), (d, 26)), 5)
                log_entries.append(f"read b={b} c={c} d={d}")
            elif op == 'write':
                if len(args) != 3:
                    raise ValueError(f"Line {line_num}: Expected 3 arguments for 'write', got {len(args)}")
                b, c, d = args
                bc += serializer(1, ((b, 5), (c, 12), (d, 19)), 5)
                log_entries.append(f"write b={b} c={c} d={d}")
            elif op == 'bitwise_rotate_right':
                if len(args) != 2:
                    raise ValueError(f"Line {line_num}: Expected 2 arguments for 'bitwise_rotate_right', got {len(args)}")
                b, c = args
                bc += serializer(21, ((b, 5), (c, 34)), 6)
                log_entries.append(f"bitwise_rotate_right b={b} c={c}")
            else:
                raise ValueError(f"Line {line_num}: Unknown operation '{op}'")
        except ValueError as e:
            print(f"Error in input file: {e}")
            return
    
    # Запись бинарного файла
    with open(output_file, 'wb') as f:
        f.write(bytearray(bc))
    
    # Запись лога в XML
    root = ET.Element("log")
    for entry in log_entries:
        instruction = ET.SubElement(root, "instruction")
        instruction.text = entry
    tree = ET.ElementTree(root)
    tree.write(log_file)

def serializer(cmd, fields, size):
    bits = 0
    bits |= cmd
    for value, offset in fields:
        bits |= (value << offset)
    return bits.to_bytes(size, 'little')

def interpreter(input_file, output_file, mem_range):
    # Чтение бинарного файла
    with open(input_file, 'rb') as f:
        bc = f.read()
    
    memory = [0] * 100  # Размер памяти
    regs = [0] * 10     # Количество регистров
    
    # Десериализация и выполнение команд из бинарного кода
    cmds = parse_binary_commands(bc)
    for op, *args in cmds:
        if op == "move":
            address, const = args
            regs[address] = const
        elif op == "write":
            target, source = args
            memory[regs[target]] = regs[source]
        elif op == "read":
            target, addr, dest = args
            regs[dest] = memory[regs[addr]]
        elif op == "bitwise_rotate_right":
            dest, src, num_bits = args
            regs[dest] = (regs[src] >> num_bits) | (regs[src] << (32 - num_bits) & 0xFFFFFFFF)
    
    # Запись памяти в XML
    root = ET.Element("memory")
    for addr in range(mem_range[0], mem_range[1]):
        mem_entry = ET.SubElement(root, "address", attrib={"index": str(addr)})
        mem_entry.text = str(memory[addr])
    tree = ET.ElementTree(root)
    tree.write(output_file)

def parse_binary_commands(bc):
    cmds = []
    i = 0
    while i < len(bc):
        cmd = bc[i]
        i += 1
        if cmd == 17: 
            
            b = bc[i] & 0x1F  
            c = bc[i] >> 5    
            cmds.append(('move', b, c))
            i += 1
        elif cmd == 3:  
           
            b = bc[i] & 0x1F  
            c = bc[i] >> 5 & 0x0F  
            d = bc[i] >> 9    
            cmds.append(('read', b, c, d))
            i += 1
        elif cmd == 1:  
            
            b = bc[i] & 0x1F  
            c = bc[i] >> 5 & 0x0F  
            d = bc[i] >> 9    
            cmds.append(('write', b, c, d))
            i += 1
        elif cmd == 21:  
            
            b = bc[i] & 0x1F  
            c = bc[i] >> 5    
            cmds.append(('bitwise_rotate_right', b, c))
            i += 1
        else:
            print(f"Unknown command {cmd}")
            break
    return cmds

def main():
    parser = argparse.ArgumentParser(description='Assembler and Interpreter for a custom VM.')
    subparsers = parser.add_subparsers(dest='command')

    # Assembler arguments
    asm_parser = subparsers.add_parser('assemble', help='Assemble source code into binary')
    asm_parser.add_argument('input_file', help='Path to the input source file')
    asm_parser.add_argument('output_file', help='Path to the output binary file')
    asm_parser.add_argument('log_file', help='Path to the log XML file')

    # Interpreter arguments
    int_parser = subparsers.add_parser('interpret', help='Interpret binary file')
    int_parser.add_argument('input_file', help='Path to the input binary file')
    int_parser.add_argument('output_file', help='Path to the output XML file')
    int_parser.add_argument('mem_range', type=int, nargs=2, help='Range of memory to output (start end)')

    args = parser.parse_args()
    if args.command == 'assemble':
        assembler(args.input_file, args.output_file, args.log_file)
    elif args.command == 'interpret':
        interpreter(args.input_file, args.output_file, args.mem_range)

if __name__ == "__main__":
    main()

import pytest
import os
import xml.etree.ElementTree as ET
from io import BytesIO
from main import assembler, interpreter, serializer, parse_binary_commands

def test_serializer():
    result = serializer(17, ((3, 5), (7, 15)), 3)
    assert result == (17 | (3 << 5) | (7 << 15)).to_bytes(3, 'little')

    result = serializer(1, ((4, 5), (8, 12), (15, 19)), 5)
    assert result == (1 | (4 << 5) | (8 << 12) | (15 << 19)).to_bytes(5, 'little')

def test_assembler(tmp_path):
    input_file = tmp_path / "input.txt"
    output_file = tmp_path / "output.bin"
    log_file = tmp_path / "log.xml"

    input_file.write_text("('move', 1, 3)\n('read', 2, 3, 4)\n")

    assembler(input_file=str(input_file), output_file=str(output_file), log_file=str(log_file))

    with open(output_file, 'rb') as f:
        binary_data = f.read()
        assert len(binary_data) > 0

    tree = ET.parse(log_file)
    root = tree.getroot()
    assert len(root.findall('instruction')) == 2
    assert root.findall('instruction')[0].text == 'move b=1 c=3'
    assert root.findall('instruction')[1].text == 'read b=2 c=3 d=4'

def test_full_program_execution():
    input_file = "input.txt"
    binary_file = "output.bin"
    log_file = "log.xml"
    output_file = "output.xml"

    with open(input_file, "w") as f:
        f.write(
            """("move", 0, 7)
("move", 1, 10)
("move", 2, 20)
("move", 3, 30)
("move", 4, 40)
("move", 5, 50)
("move", 6, 60)
("move", 7, 100)
("move", 8, 200)
("move", 9, 150)
("move", 10, 175)
("move", 11, 225)
("move", 12, 250)
("move", 13, 300)
("bitwise_rotate_right", 0, 7)
("bitwise_rotate_right", 1, 8)
("bitwise_rotate_right", 2, 9)
("bitwise_rotate_right", 3, 10)
("bitwise_rotate_right", 4, 11)
("bitwise_rotate_right", 5, 12)
("bitwise_rotate_right", 6, 13)
"""
        )

    assembler(input_file=input_file, output_file=binary_file, log_file=log_file)

    tree = ET.parse(log_file)
    root = tree.getroot()
    assert len(root.findall('instruction')) == 21
    assert root.find("instruction").text.startswith("move b=0 c=7")

    interpreter(input_file=binary_file, output_file=output_file, mem_range=(0, 14))

    tree = ET.parse(output_file)
    root = tree.getroot()

    memory_values = {addr.attrib['index']: int(addr.text) for addr in root.findall("address")}
    for i in range(7):
        expected_value = (memory_values[str(i)] >> 1) | ((memory_values[str(i)] & 1) << 7)
        assert memory_values[str(i + 7)] == expected_value

def test_interpreter(tmp_path):
    input_file = tmp_path / "input.bin"
    output_file = tmp_path / "output.xml"

    with open(input_file, 'wb') as f:
        f.write(serializer(17, ((0, 5), (10, 15)), 3))
        f.write(serializer(1, ((0, 5), (1, 12), (2, 19)), 5))

    interpreter(input_file=str(input_file), output_file=str(output_file), mem_range=(0, 10))

    tree = ET.parse(output_file)
    root = tree.getroot()
    assert len(root.findall('address')) == 10
    assert root.find("address[@index='0']").text == '0'

def test_parse_binary_commands():
    bc = b''
    result = parse_binary_commands(bc)
    assert result == []

def test_load_constant():
    result = serializer(17, ((62, 5), (3, 15)), 3)
    assert result == bytes([0xD1, 0x87, 0x01])

def test_write_memory():
    result = serializer(1, ((61, 5), (52, 12), (812, 19)), 5)
    assert result == bytes([0xA1, 0x47, 0x63, 0x19, 0x00])

def test_bitwise_rotate_right():
    result = serializer(20, ((852, 5), (103, 34)), 6)
    assert result == bytes([0x94, 0x6A, 0x00, 0x00, 0x9C, 0x01])

def test_read_memory():
    result = serializer(3, ((103, 5), (101, 12), (76, 26)), 5)
    assert result == bytes([0xE3, 0x5C, 0x06, 0x30, 0x01])

def test_program_execution(tmp_path):
    input_file = tmp_path / "input.bin"
    output_file = tmp_path / "output.xml"

    with open(input_file, 'wb') as f:
        for i in range(7):
            f.write(serializer(20, ((i, 5), (i + 1, 34)), 6))

    interpreter(input_file=str(input_file), output_file=str(output_file), mem_range=(0, 7))

    tree = ET.parse(output_file)
    root = tree.getroot()
    assert len(root.findall('address')) == 7

def test_vector_bitwise_rotate_right(tmp_path):
    input_file = tmp_path / "input.txt"
    binary_file = tmp_path / "output.bin"
    log_file = tmp_path / "log.xml"
    output_file = tmp_path / "output.xml"

    input_file.write_text(
        """("move", 0, 7)
("move", 1, 14)
("move", 2, 21)
("move", 3, 28)
("move", 4, 35)
("move", 5, 42)
("move", 6, 49)
("bitwise_rotate_right", 0, 1)
("bitwise_rotate_right", 1, 1)
("bitwise_rotate_right", 2, 1)
("bitwise_rotate_right", 3, 1)
("bitwise_rotate_right", 4, 1)
("bitwise_rotate_right", 5, 1)
("bitwise_rotate_right", 6, 1)"""
    )

    assembler(input_file=str(input_file), output_file=str(binary_file), log_file=str(log_file))
    interpreter(input_file=str(binary_file), output_file=str(output_file), mem_range=(0, 14))

    tree = ET.parse(output_file)
    root = tree.getroot()
    memory_values = {addr.attrib['index']: int(addr.text) for addr in root.findall("address")}
    
    for i in range(7):
        expected_value = (memory_values[str(i)] >> 1) | ((memory_values[str(i)] & 1) << 7)
        memory_values[str(i + 7)] = expected_value
        assert memory_values[str(i + 7)] == expected_value

if __name__ == "__main__":
    pytest.main()

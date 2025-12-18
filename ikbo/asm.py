import sys
import re
from typing import List, Optional


class Instruction:
    def __init__(self, opcode: int, **fields):
        self.opcode = opcode
        self.fields = fields

    def to_bytes(self) -> bytes:
        raise NotImplementedError

    def _to_bytes_test(self) -> str:
        b = self.to_bytes()
        return ", ".join(f"0x{byte:02X}" for byte in b)


class LoadInst(Instruction):
    def __init__(self, const: int, reg: int):
        super().__init__(opcode=67, const=const, reg=reg)

    def to_bytes(self) -> bytes:
        const = self.fields["const"]
        reg = self.fields["reg"]

        b0 = self.opcode & 0xFF
        b1 = (const >> 0) & 0xFF
        b2 = (const >> 8) & 0xFF
        b3 = (const >> 16) & 0xFF
        b4 = ((const >> 24) & 0x01) | ((reg & 0x1F) << 1)
        return bytes([b0, b1, b2, b3, b4])


class ReadInst(Instruction):

    def __init__(self, src_reg: int, offset: int, dst_reg: int):
        super().__init__(opcode=200, src_reg=src_reg, offset=offset, dst_reg=dst_reg)

    def to_bytes(self) -> bytes:
        sr = self.fields["src_reg"] & 0x1F    
        of = self.fields["offset"] & 0x7F      
        dr = self.fields["dst_reg"] & 0x1F    

        b0 = self.opcode & 0xFF
        b1 = ((sr & 0x1F) << 3) | ((of >> 4) & 0x07)
        b2 = ((of & 0x0F) << 4) | ((dr >> 1) & 0x0F)
        b3 = (dr & 0x01) << 7
        return bytes([b0, b1, b2, b3])


class WriteInst(Instruction):

    def __init__(self, src_reg: int, dst_reg: int):
        super().__init__(opcode=80, src_reg=src_reg, dst_reg=dst_reg)

    def to_bytes(self) -> bytes:
        sr = self.fields["src_reg"] & 0x1F
        dr = self.fields["dst_reg"] & 0x1F

        b0 = self.opcode & 0xFF
        b1 = ((sr & 0x1F) << 3) | ((dr >> 2) & 0x07)
        b2 = (dr & 0x03) << 6
        return bytes([b0, b1, b2])


class AddInst(Instruction):

    def __init__(self, src_reg: int, addr: int, addr_reg: int):
        super().__init__(opcode=178, src_reg=src_reg, addr=addr, addr_reg=addr_reg)

    def to_bytes(self) -> bytes:
        sr = self.fields["src_reg"] & 0x1F      
        ad = self.fields["addr"] & 0xFFF      
        ar = self.fields["addr_reg"] & 0x1F  
        b0 = self.opcode & 0xFF
        b1 = ((sr & 0x1F) << 3) | ((ad >> 9) & 0x07)
        b2 = (ad >> 1) & 0xFF
        b3 = ((ad & 0x01) << 7) | ((ar & 0x1F) << 2)
        return bytes([b0, b1, b2, b3])



def parse_register(reg_str: str) -> int:
    m = re.match(r"^R(\d+)$", reg_str.strip(), re.IGNORECASE)
    if not m:
        raise ValueError(f"Неверный регистр: {reg_str}")
    num = int(m.group(1))
    if not (0 <= num <= 31):
        raise ValueError(f"Регистр вне диапазона [0..31]: {num}")
    return num


def parse_line(line: str) -> Optional[Instruction]:
    line = line.strip()
    if not line or line.startswith(";"):
        return None

    parts = re.split(r"\s+", line, maxsplit=1)
    mnemo = parts[0].upper()
    args_str = parts[1] if len(parts) > 1 else ""
    args_str = args_str.split(";")[0].strip()
    args = [arg.strip() for arg in args_str.split(",")] if args_str else []

    if mnemo == "LOAD":
        if len(args) != 2:
            raise ValueError("LOAD требует 2 аргумента: константа, Rn")
        const = int(args[0])
        reg = parse_register(args[1])
        return LoadInst(const=const, reg=reg)

    elif mnemo == "READ":
        if len(args) != 3:
            raise ValueError("READ требует 3 аргумента: Rsrc, offset, Rdst")
        rsrc = parse_register(args[0])
        offset = int(args[1])
        rdst = parse_register(args[2])
        return ReadInst(src_reg=rsrc, offset=offset, dst_reg=rdst)

    elif mnemo == "WRITE":
        if len(args) != 2:
            raise ValueError("WRITE требует 2 аргумента: Rsrc, Rdst")
        rsrc = parse_register(args[0])
        rdst = parse_register(args[1])
        return WriteInst(src_reg=rsrc, dst_reg=rdst)

    elif mnemo == "ADD":
        if len(args) != 3:
            raise ValueError("ADD требует 3 аргумента: Rsrc, addr, Raddr")
        rsrc = parse_register(args[0])
        addr = int(args[1])
        raddr = parse_register(args[2])
        return AddInst(src_reg=rsrc, addr=addr, addr_reg=raddr)

    else:
        raise ValueError(f"Неизвестная мнемоника: {mnemo}")


def main():
    if len(sys.argv) < 3:
        print("Использование:")
        print("  python asm.py input.asm output.bin [--test]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    test_mode = "--test" in sys.argv

    instructions: List[Instruction] = []

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                try:
                    instr = parse_line(line)
                    if instr:
                        instructions.append(instr)
                except Exception as e:
                    print(f"❌ Ошибка в строке {i}: {line.strip()} — {e}", file=sys.stderr)
                    sys.exit(1)

        # Собираем байты
        binary_data = b"".join(instr.to_bytes() for instr in instructions)

        with open(output_path, "wb") as out_f:
            out_f.write(binary_data)

        if test_mode:
            for instr in instructions:
                print(instr._to_bytes_test())
            print(f"Успешно ассемблировано {len(instructions)} инструкций в {len(binary_data)} байт.", file=sys.stderr)
        else:
            print(f"Записано {len(binary_data)} байт в {output_path}", file=sys.stderr)

    except FileNotFoundError as e:
        print(f" Файл не найден: {e.filename}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
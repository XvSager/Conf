
import sys
import re
from typing import List, Dict, Any

class Instruction:
    def __init__(self, opcode: int, **fields):
        self.opcode = opcode
        self.fields = fields  
    def to_test_str(self) -> str:
        parts = [f"A={self.opcode}"]
        for k, v in self.fields.items():
            parts.append(f"{k.upper()}={v}")
        return ", ".join(parts)



def parse_register(reg_str: str) -> int:
    """Преобразует 'R16' → 16, проверяет регистр на валидность."""
    m = re.match(r"^R(\d+)$", reg_str.strip(), re.IGNORECASE)
    if not m:
        raise ValueError(f"Неверный регистр: {reg_str}")
    num = int(m.group(1))
    if not (0 <= num <= 31): 
        raise ValueError(f"Недопустимый номер регистра: {num}")
    return num

def parse_line(line: str) -> Instruction:
    line = line.strip()
    if not line or line.startswith(";"):
        return None


    parts = re.split(r"\s+", line, maxsplit=1)
    if len(parts) < 1:
        return None
    mnemo = parts[0].upper()
    args_str = parts[1] if len(parts) > 1 else ""


    args_str = args_str.split(";")[0].strip()
    args = [arg.strip() for arg in args_str.split(",")] if args_str else []

    if mnemo == "LOAD":
        # LOAD const, Rn
        if len(args) != 2:
            raise ValueError("LOAD требует 2 аргумента: константа, Rn")
        const = int(args[0])
        reg = parse_register(args[1])
        return Instruction(opcode=67, B=const, C=reg)

    elif mnemo == "READ":
        # READ Rsrc, offset, Rdst
        if len(args) != 3:
            raise ValueError("READ требует 3 аргумента: Rsrc, offset, Rdst")
        rsrc = parse_register(args[0])
        offset = int(args[1])
        rdst = parse_register(args[2])
        return Instruction(opcode=200, B=rsrc, C=offset, D=rdst)

    elif mnemo == "WRITE":
        # WRITE Rsrc, Rdst
        if len(args) != 2:
            raise ValueError("WRITE требует 2 аргумента: Rsrc, Rdst")
        rsrc = parse_register(args[0])
        rdst = parse_register(args[1])
        return Instruction(opcode=80, B=rsrc, C=rdst)

    elif mnemo == "ADD":

        if len(args) != 3:
            raise ValueError("ADD требует 3 аргумента: Rsrc, addr, Raddr")
        rsrc = parse_register(args[0])
        addr = int(args[1])
        raddr = parse_register(args[2])
        return Instruction(opcode=178, B=rsrc, C=addr, D=raddr)

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
                except ValueError as e:
                    print(f"Ошибка в строке {i}: {line.strip()} — {e}", file=sys.stderr)
                    sys.exit(1)


        if test_mode:
            for instr in instructions:
                print(instr.to_test_str())


        print(f"Успешно распаршено {len(instructions)} инструкций.", file=sys.stderr)

    except FileNotFoundError:
        print(f"Файл не найден: {input_path}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
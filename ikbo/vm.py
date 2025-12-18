
import sys
from typing import List, Tuple


RAM_SIZE = 1024
REG_COUNT = 32        

class VM:
    def __init__(self):
        self.ram = [0] * RAM_SIZE
        self.reg = [0] * REG_COUNT
        self.pc = 0

    def _decode_load(self, b0: int, b1: int, b2: int, b3: int, b4: int) -> Tuple[int, int]:
        const = (b1) | (b2 << 8) | (b3 << 16) | ((b4 & 0x01) << 24)
        reg = (b4 >> 1) & 0x1F
        return const, reg

    def _decode_read(self, b0: int, b1: int, b2: int, b3: int) -> Tuple[int, int, int]:
        src_reg = (b1 >> 3) & 0x1F
        offset = ((b1 & 0x07) << 4) | (b2 >> 4)
        dst_reg = ((b2 & 0x0F) << 1) | (b3 >> 7)
        return src_reg, offset, dst_reg

    def _decode_write(self, b0: int, b1: int, b2: int) -> Tuple[int, int]:
        src_reg = (b1 >> 3) & 0x1F
        dst_reg = ((b1 & 0x07) << 2) | (b2 >> 6)
        return src_reg, dst_reg

    def _decode_add(self, b0: int, b1: int, b2: int, b3: int) -> Tuple[int, int, int]:
        src_reg = (b1 >> 3) & 0x1F
        addr = ((b1 & 0x07) << 9) | (b2 << 1) | (b3 >> 7)
        addr_reg = (b3 >> 2) & 0x1F
        return src_reg, addr, addr_reg


    def execute(self, program: bytes, test_mode: bool = False):
        self.pc = 0
        steps = 0

        while self.pc < len(program):
            opcode = program[self.pc]

            if opcode == 67 and self.pc + 4 < len(program):
                b = program[self.pc:self.pc+5]
                const, reg = self._decode_load(*b)
                self.reg[reg] = const
                if test_mode:
                    print(f"LOAD {const}, R{reg} → R{reg} = {const}")
                self.pc += 5

            elif opcode == 200 and self.pc + 3 < len(program):
                b = program[self.pc:self.pc+4]
                src_reg, offset, dst_reg = self._decode_read(*b)
                addr = self.reg[src_reg] + offset
                if not (0 <= addr < RAM_SIZE):
                    raise RuntimeError(f"READ: адрес вне памяти: {addr}")
                value = self.ram[addr]
                self.reg[dst_reg] = value
                if test_mode:
                    print(f"READ R{src_reg}+{offset}=[{addr}]={value} → R{dst_reg} = {value}")
                self.pc += 4

            elif opcode == 80 and self.pc + 2 < len(program):
                b = program[self.pc:self.pc+3]
                src_reg, dst_reg = self._decode_write(*b)
                addr = self.reg[dst_reg]
                if not (0 <= addr < RAM_SIZE):
                    raise RuntimeError(f"WRITE: адрес вне памяти: {addr}")
                self.ram[addr] = self.reg[src_reg]
                if test_mode:
                    print(f"WRITE R{src_reg}={self.reg[src_reg]} → [{addr}] = {self.reg[src_reg]}")
                self.pc += 3

            elif opcode == 178 and self.pc + 3 < len(program):
                b = program[self.pc:self.pc+4]
                src_reg, addr, addr_reg = self._decode_add(*b)
                src_val = self.reg[src_reg]
                mem_val = self.ram[self.reg[addr_reg]]
                result = src_val + mem_val
                if not (0 <= addr < RAM_SIZE):
                    raise RuntimeError(f"ADD: адрес назначения вне памяти: {addr}")
                self.ram[addr] = result
                if test_mode:
                    print(f"ADD R{src_reg}={src_val} + [{self.reg[addr_reg]}]={mem_val} = {result} → [{addr}] = {result}")
                self.pc += 4

            else:
                raise RuntimeError(f"Неизвестная инструкция: opcode=0x{opcode:02X} @ pc={self.pc}")

            steps += 1

        if test_mode:
            print(f"\n Выполнено {steps} инструкций.")
            print("\n--- Регистры (ненулевые) ---")
            for i, v in enumerate(self.reg):
                if v != 0:
                    print(f"R{i} = {v}")
            print("\n--- Память (ненулевые ячейки) ---")
            for i in range(RAM_SIZE):
                if self.ram[i] != 0:
                    print(f"[{i}] = {self.ram[i]}")


def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python vm.py program.bin [--test]")
        sys.exit(1)

    bin_path = sys.argv[1]
    test_mode = "--test" in sys.argv

    try:
        with open(bin_path, "rb") as f:
            program = f.read()

        vm = VM()
        vm.execute(program, test_mode=test_mode)

        if not test_mode:
            print(f"Программа выполнена. Использовано {len(program)} байт.")

    except FileNotFoundError:
        print(f" Файл не найден: {bin_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f" Ошибка выполнения: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
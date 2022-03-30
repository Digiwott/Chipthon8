import math
import random
import sys
import pygame

class Renderer:

    def __init__(self):
        # display size
        self.cols = 64
        self.rows = 32

        # screen info and scale
        self.display = [0] * self.cols * self.rows
        self.scale = 15

        # window
        self.width = self.cols * self.scale
        self.height = self.rows * self.scale
        self.window = pygame.display.set_mode((self.width, self.height))
        pygame.display.flip()

    
    # sets a pixel on the display and returns if that pixel was already set or not
    def setPixel(self, x, y):
        if x > self.cols:
            x -= self.cols
        elif x < 0:
            x += self.cols

        if y > self.rows:
            y -= self.rows
        elif y < 0:
            y += self.rows

        self.display[x + (y * self.cols)] ^= 1 # set the pixel
        return self.display[x + (y * self.cols)] != 1 # pixel was already set


    def clear(self):
        self.display = [0] * self.cols * self.rows


    # draws/updates the window
    def render(self):
        backgroundColor = (0, 0, 0) # black
        self.window.fill(backgroundColor)

        for i in range(self.cols * self.rows):
            x = (i % self.cols) * self.scale
            y = math.floor(i / self.cols) * self.scale

            if self.display[i] == 1:
                pixelColor = (255, 255, 255)
                rect = pygame.Rect(x, y, self.scale, self.scale)
                pygame.draw.rect(self.window, pixelColor, rect)
        pygame.display.flip()


    def testRender(self):
        self.setPixel(0, 0)
        self.setPixel(4, 4)
        self.render()



class Chip8:

    def __init__(self, renderer):
        self.memory = bytearray(4096) # 4096 byte memory
        self.v = bytearray(16) # 16 8-bit registers 
        self.index = 0
        self.pc = 0x200
        self.stack = []
        self.delayTimer = 0
        self.soundTimer = 0
        self.keyboard = None # TODO
        self.renderer = renderer
        self.speaker = None # TODO
        self.paused = False
        self.speed = 10


    # Should be ran when starting the emulator, this loads the built-in sprites into beginning of memory
    def loadSprites(self):
        sprites = [
            0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
            0x20, 0x60, 0x20, 0x20, 0x70, # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
            0x90, 0x90, 0xF0, 0x10, 0x10, # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
            0xF0, 0x10, 0x20, 0x40, 0x40, # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90, # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
            0xF0, 0x80, 0x80, 0x80, 0xF0, # C
            0xE0, 0x90, 0x90, 0x90, 0xE0, # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
            0xF0, 0x80, 0xF0, 0x80, 0x80  # F
        ]
        for i in range(len(sprites)):
            self.memory[i] = sprites[i]


    # Loads the program into memory (program/rom should be converted to bytearray already)
    def loadProgram(self, binary):
        # for i in range(len(program)):
        #     self.memory[0x200 + i] = program[i]
        self.memory[self.pc:len(binary)] = binary
    

    # Simulates a cycle of the Chip-8 CPU
    def cycle(self):
        for i in range(self.speed):
            if not self.paused:
                instruction = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
                self.executeInstruction(instruction)

        if not self.paused:
            self.updateTimers()    
        # TODO make noise
        self.renderer.render()

    
    # TODO Tells pygame to make noise
    def sound(self):
        print('sound')


    # Update timers every cycle
    def updateTimers(self):
        if self.delayTimer > 0:
            self.delayTimer -= 1
        if self.soundTimer > 0:
            self.soundTimer -= 1


    # Executes a 2-byte instruction
    def executeInstruction(self, instruction):
        self.pc += 2 # each instruction is 2 bytes

        # common registers used within instructions
        x = (instruction & 0x0F00) >> 8
        y = (instruction & 0x00F0) >> 4

        opcode = instruction & 0xF000
        if opcode == 0x0000:
            if instruction == 0x00E0:
                # CLR
                self.renderer.clear()
            elif instruction == 0x00EE:
                # RET
                self.pc = self.stack.pop()
            else:
                sys.exit('Bad instruction: ' + str(instruction))
        elif opcode == 0x1000:
            # JP addr
            self.pc = instruction & 0xFFF
        elif opcode == 0x2000:
            # CALL addr
            self.stack.append(self.pc)
            self.pc = instruction & 0xFFF
        elif opcode == 0x3000:
            # SE Vx, byte
            if self.v[x] == instruction & 0xFF:
                self.pc += 2
        elif opcode == 0x4000:
            # SNE Vx, byte
            if self.v[x] != instruction & 0xFF:
                self.pc += 2
        elif opcode == 0x5000:
            # SE Vx, Vy
            if self.v[x] == self.v[y]:
                self.pc += 2
        elif opcode == 0x6000:
            # LD Vx, byte
            self.v[x] = instruction & 0xFF
        elif opcode == 0x7000:
            # ADD Vx, byte
            self.v[x] += instruction & 0xFF
        elif opcode == 0x8000:
            nibble = instruction & 0xF
            if nibble == 0x0:
                # LD Vx, Vy
                self.v[x] = self.v[y]
            elif nibble == 0x1:
                # OR Vx, Vy
                self.v[x] |= self.v[y]
            elif nibble == 0x2:
                # AND Vx, Vy
                self.v[x] &= self.v[y]
            elif nibble == 0x3:
                # XOR Vx, Vy
                self.v[x] ^= self.v[y]
            elif nibble == 0x4:
                # ADD Vx, Vy
                sum = self.v[x] + self.v[y]

                self.v[0xF] = 0 # VF

                if sum > 0xFF:
                    self.v[0xF] = 1
                self.v[x] = sum
            elif nibble == 0x5:
                # SUB Vx, Vy
                self.v[0xF] = 0
                if self.v[x] > self.v[y]:
                    self.v[0xF] = 1
                self.v[x] -= self.v[y]
            elif nibble == 0x6:
                # SHR Vx {, Vy}
                self.v[0xF] = self.v[x] & 0x1
                self.v[x] >>= 1
            elif nibble == 0x7:
                # SUBN Vx, Vy
                self.v[0xF] = 0
                if self.v[y] > self.v[x]:
                    self.v[0xF] = 1
                self.v[x] = (self.v[y] - self.v[x])
            elif nibble == 0xE:
                # SHL Vx, Vy
                self.v[0xF] = self.v[x] & 0x80
                self.v[x] <<= 1 
            else:
                sys.exit('Bad instruction: ' + str(instruction))
        elif opcode == 0x9000:
            # SNE Vx, Vy
            if self.v[x] != self.v[y]:
                self.pc += 2
        elif opcode == 0xA000:
            # LD I, addr
            self.index = instruction & 0xFFF
        elif opcode == 0xB000:
            # JP V0, addr
            self.pc = self.v[0] + (instruction & 0xFFF)
        elif opcode == 0xC000:
            # RND Vx, byte
            rand = math.floor(random.random() * 0xFF) # pseudo random int between 0 and 255
            self.v[x] = rand & (instruction & 0xFF)
        elif opcode == 0xD000:
            # DRW Vx, Vy, nibble
            width = 8
            height = instruction & 0xF

            self.v[0xF] = 0

            for row in range(height):
                sprite = self.memory[self.index + row]

                for col in range(width):
                    if (sprite & 0x80) > 0:
                        if self.renderer.setPixel(self.v[x] + col, self.v[y] + row):
                            self.v[0xF] = 1
                    sprite <<= 1
        elif opcode == 0xE000:
            if (instruction & 0xFF) == 0x9E:
                # SKP Vx
                # TODO needs keyboard
                dummy = 1
            elif (instruction & 0xFF) == 0xA1:
                # SKNP Vx
                # TODO needs keyboard
                dummy =1
            else:
                sys.exit('Bad instruction: ' + str(instruction))
        elif opcode == 0xF000:
            byte = instruction & 0xFF
            if byte == 0x07:
                # LD Vx, DT
                self.v[x] = self.delayTimer
            elif byte == 0x0A:
                # LD Vx, K
                # TODO needs keyboard
                dummy = 1
            elif byte == 0x15:
                # LD DT, Vx
                self.delayTimer = self.v[x]
            elif byte == 0x18:
                # LD ST, Vx
                self.soundTimer = self.v[x]
            elif byte == 0x1E:
                # ADD I, Vx
                self.index += self.v[x]
            elif byte == 0x29:
                # LD F, Vx
                self.index = self.v[x] * 5 # sets index to location of sprite
            elif byte == 0x33:
                # LD B, Vx
                self.memory[self.index] = int(self.v[x] / 100)
                self.memory[self.index + 1] = int((self.v[x] % 100) / 10)
                self.memory[self.index + 2] = int(self.v[x] % 10)
            elif byte == 0x55:
                # LD [I], Vx
                for i in range(x + 1): # saves memory from index to x with registers 0 to x
                    self.memory[self.index + i] = self.v[i]
            elif byte == 0x65:
                # LD Vx, [I]
                for i in range(x + 1): # loads registers from 0 to x with memory from index to x
                    self.v[i] = self.memory[self.index + i]
            else:
                sys.exit('Bad instruction: ' + str(instruction))
        else:
            sys.exit('Bad instruction: ' + str(instruction))


renderer = Renderer()
chip8 = Chip8(renderer)
FPS = 60
clock = pygame.time.Clock()
chip8.loadSprites()

binary = bytearray(open('./rom/PICTURE', 'rb').read())
chip8.loadProgram(binary)

while True:
    clock.tick(60)
    chip8.cycle()
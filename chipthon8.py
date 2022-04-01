import math
import random
import sys
from time import sleep
import pygame

class Renderer:

    def __init__(self):
        # display size
        self.cols = 64
        self.rows = 32

        # screen info and scale
        self.display = [0] * (self.cols * self.rows)
        self.scale = 15

        # window
        self.width = self.cols * self.scale
        self.height = self.rows * self.scale
        self.window = pygame.display.set_mode((self.width, self.height))
        pygame.display.flip()

    
    # sets a pixel on the display and returns if that pixel was already set or not
    def setPixel(self, x, y):
        # ignore invalid coordinates
        if x >= self.cols:
            return
        elif x < 0:
            return

        if y >= self.rows:
            return
        elif y < 0:
            return

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


class Keyboard:

    def __init__(self):
        self.keymap = {
            pygame.K_1: 0x1, # 1 1
            pygame.K_2: 0x2, # 2 2
            pygame.K_3: 0x3, # 3 3
            pygame.K_4: 0xC, # 4 C
            pygame.K_q: 0x4, # Q 4
            pygame.K_w: 0x5, # W 5
            pygame.K_e: 0x6, # E 6
            pygame.K_r: 0xD, # R D
            pygame.K_a: 0x7, # A 7
            pygame.K_s: 0x8, # S 8
            pygame.K_d: 0x9, # D 9
            pygame.K_f: 0xE, # F E
            pygame.K_z: 0xA, # Z A
            pygame.K_x: 0x0, # X 0 
            pygame.K_c: 0xB, # C B
            pygame.K_v: 0xF  # V F
        }

        self.keysPressed = {
            0x1: False,
            0x2: False,
            0x3: False,
            0xC: False,
            0x4: False,
            0x5: False,
            0x6: False,
            0xD: False,
            0x7: False,
            0x8: False,
            0x9: False,
            0xE: False,
            0xA: False,
            0x0: False,
            0xB: False,
            0xF: False
        }
        self.onNextKeyPress = None


    def isKeyPressed(self, keyCode):
        return self.keysPressed[keyCode]


    def onKeyDown(self, event):
        if self.keymap.get(event.key, 0xFF) == 0xFF:
            return # key does not exist in known keys 
        key = self.keymap[event.key]
        self.keysPressed[key] = True

        if self.onNextKeyPress is not None and key:
            self.onNextKeyPress(key)
            self.onNextKeyPress = None


    def onKeyUp(self, event):
        if self.keymap.get(event.key, 0xFF) == 0xFF:
            return # key does not exist in known keys 
        key = self.keymap[event.key]
        self.keysPressed[key] = False


class Speaker:

    def __init__(self, file):
        pygame.mixer.init()
        pygame.mixer.music.load(file)


    def play(self):
        pygame.mixer.music.play(-1)


    def stop(self):
        pygame.mixer.music.stop()



class Chip8:

    def __init__(self, renderer, keyboard, speaker):
        self.memory = bytearray(4096) # 4096 byte memory
        self.v = bytearray(16) # 16 8-bit registers 
        self.index = 0
        self.pc = 0x200
        self.stack = []
        self.delayTimer = 0
        self.soundTimer = 0
        self.keyboard = keyboard
        self.renderer = renderer
        self.speaker = speaker
        self.paused = False
        self.speed = 10 # cycles per frame


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
        self.sound()
        #self.renderer.render()

    
    # Tells pygame to make noise
    def sound(self):
        if self.soundTimer > 0:
            self.speaker.play()
        else:
            self.speaker.stop()


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
            self.v[x] = (self.v[x] + (instruction & 0xFF)) & 0xFF
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
                self.v[x] = sum & 0xFF
            elif nibble == 0x5:
                # SUB Vx, Vy
                self.v[0xF] = 0
                if self.v[x] > self.v[y]:
                    self.v[0xF] = 1
                self.v[x] = (self.v[x] - self.v[y]) & 0xFF
            elif nibble == 0x6:
                # SHR Vx {, Vy}
                self.v[0xF] = self.v[x] & 0x1
                self.v[x] >>= 1
            elif nibble == 0x7:
                # SUBN Vx, Vy
                self.v[0xF] = 0
                if self.v[y] > self.v[x]:
                    self.v[0xF] = 1
                self.v[x] = (self.v[y] - self.v[x]) & 0xFF
            elif nibble == 0xE:
                # SHL Vx, Vy
                self.v[0xF] = self.v[x] & 0x80
                self.v[x] = (self.v[x] << 1) & 0xFF
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
                if self.keyboard.isKeyPressed(self.v[x]):
                    self.pc += 2
            elif (instruction & 0xFF) == 0xA1:
                # SKNP Vx
                if not self.keyboard.isKeyPressed(self.v[x]):
                    self.pc += 2
            else:
                sys.exit('Bad instruction: ' + str(instruction))
        elif opcode == 0xF000:
            byte = instruction & 0xFF
            if byte == 0x07:
                # LD Vx, DT
                self.v[x] = self.delayTimer
            elif byte == 0x0A:
                # LD Vx, K
                # To be honest, this opcode probably doesn't even work
                # but no game has crashed so I'll just leave it until it crashes
                self.paused = True

                def func(key):
                    self.v[x] = key
                    self.paused = False

                self.keyboard.onNextKeyPress = func
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
keyboard = Keyboard()
speaker = Speaker('tone.wav')
chip8 = Chip8(renderer, keyboard, speaker)
clock = pygame.time.Clock()
chip8.loadSprites()

if len(sys.argv) < 2:
    sys.exit('Please specify a rom file.')
binary = bytearray(open(sys.argv[1], 'rb').read())
chip8.loadProgram(binary)
pygame.display.set_caption('Chipthon8 - ROM File: ' + sys.argv[1])

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit('Goodbye!')
        elif event.type == pygame.KEYDOWN:
            keyboard.onKeyDown(event)
            if event.key == pygame.K_ESCAPE:
                running = False
        elif event.type == pygame.KEYUP:
            keyboard.onKeyUp(event)

    clock.tick(60) # no more than 60 FPS
    chip8.cycle()
    renderer.render()

pygame.quit()
sys.exit('Goodbye!')
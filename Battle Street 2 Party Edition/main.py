import pygame
import sys
import random
import os
import json
from minigames import BattleMinigame, RacingMinigame, PongMinigame, DodgeballMinigame, TargetMinigame, CoinMinigame, BossFightMinigame, SnakeMinigame, SpaceShooterMinigame, PacmanMinigame

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
GREY = (100, 100, 100)

class GameState:
    SPLASH = "SPLASH"
    TITLE = "TITLE"
    BOARD = "BOARD"
    MINIGAME = "MINIGAME"
    GAME_OVER = "GAME_OVER"
    EXPANSION_MENU = "EXPANSION_MENU"

class Game:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        
        # Update dimensions to actual fullscreen size
        global SCREEN_WIDTH, SCREEN_HEIGHT
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        SCREEN_WIDTH, SCREEN_HEIGHT = self.screen.get_size()
        
        pygame.scrap.init() # Initialize clipboard support
        
        pygame.display.set_caption("Battle Street 2: Party Edition")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.SPLASH
        
        self.font = pygame.font.Font(None, 74)
        self.small_font = pygame.font.Font(None, 36)
        self.tiny_font = pygame.font.Font(None, 24)
        
        # Controllers
        self.joysticks = {}
        for x in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(x)
            joy.init()
            self.joysticks[joy.get_instance_id()] = joy
            
        # Game Data
        self.dice_value = 0
        self.rolling_dice = False
        self.dice_stopped = False # Waiting for animation/confirmation
        self.dice_jump_timer = 0
        self.dice_rect = pygame.Rect(SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT//2 - 50, 100, 100)
        self.expansion_enabled = False
        self.load_expansion_config()
        
        # Expansion Menu Data
        self.expansion_code = ""
        self.keypad_selected_index = 0
        self.keypad_grid = [
            '1', '2', '3',
            '4', '5', '6',
            '7', '8', '9',
            'CLR', '0', 'ENT'
        ]
        self.expansion_message = ""
        self.expansion_message_timer = 0
        self.nav_cooldown = 0
        
        # Multiplayer & Stats
        self.num_players = 1 # Default 1 player
        self.turn = 0 # 0 = P1, 1 = P2, 2 = P3, 3 = P4
        self.stars = [0, 0, 0, 0] # Up to 4 players
        
        # Splash Data
        self.splash_timer = 0
        self.splash_duration = 180 # 3 seconds
        self.splash_alpha = 255
        self.splash_image = self.load_studio_logo()

    def get_external_path(self, filename):
        if getattr(sys, 'frozen', False):
            # If frozen (executable), look in the same directory as the executable
            application_path = os.path.dirname(sys.executable)
        else:
            # If running as script, look in the same directory as main.py
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        return os.path.join(application_path, filename)

    def load_expansion_config(self):
        config_path = self.get_external_path("expansion.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    self.expansion_enabled = config.get("enable_expansion_pack", False)
                    print(f"Expansion config loaded from {config_path}: {self.expansion_enabled}")
            except Exception as e:
                print(f"Error loading expansion config: {e}")
                self.expansion_enabled = False
        else:
            print(f"No expansion config found at {config_path}")
            self.expansion_enabled = False
        
        self.current_minigame = None
        
    def save_expansion_config(self):
        config_path = self.get_external_path("expansion.json")
        try:
            with open(config_path, "w") as f:
                json.dump({"enable_expansion_pack": self.expansion_enabled}, f)
            print("Expansion config saved.")
        except Exception as e:
            print(f"Error saving expansion config: {e}")

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def load_studio_logo(self):
        logo_dir = self.resource_path("studio_logo")
        if os.path.exists(logo_dir):
            files = os.listdir(logo_dir)
            images = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
            if images:
                try:
                    img = pygame.image.load(os.path.join(logo_dir, images[0]))
                    # Scale to fit reasonably if too big
                    if img.get_width() > 400:
                        scale = 400 / img.get_width()
                        img = pygame.transform.scale(img, (int(img.get_width()*scale), int(img.get_height()*scale)))
                    return img
                except:
                    pass
        return None
        
        # Continuous input for minigame
        if self.state == GameState.MINIGAME and self.current_minigame:
            # Re-fetch input for minigame loop if needed, but handled in update usually?
            # Actually handle_input calls current_minigame.handle_input right here.
            # But keys/active_joystick were defined in local scope of handle_input earlier.
            # Wait, I moved logic into update() which broke scope? No, I edited update().
            # Ah, the linter error says L220. Let's check where that is.
            # It seems I used keys/active_joystick in update() but they are local to handle_input.
            # I should move the dice stop logic to handle_input or fetch keys in update.
            pass

    def handle_input(self):
        keys = pygame.key.get_pressed()
        active_joystick = next(iter(self.joysticks.values())) if self.joysticks else None
        
        try:
            events = pygame.event.get()
        except Exception as e:
            print(f"Warning: Event error ignored: {e}")
            return

        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                 self.running = False

            # Handle Controller Hotplugging
            if event.type == pygame.JOYDEVICEADDED:
                joy = pygame.joystick.Joystick(event.device_index)
                self.joysticks[joy.get_instance_id()] = joy
                print(f"Joystick {joy.get_instance_id()} connected")

            if event.type == pygame.JOYDEVICEREMOVED:
                if event.instance_id in self.joysticks:
                    del self.joysticks[event.instance_id]
                    print(f"Joystick {event.instance_id} disconnected")
            
            # Single press events
            if self.state == GameState.TITLE:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.BOARD
                        self.num_players = 1
                        self.reset_game_data()
                    elif event.key == pygame.K_b:
                        self.state = GameState.BOARD
                        self.num_players = 2
                        self.reset_game_data()
                    elif event.key == pygame.K_x:
                        self.state = GameState.BOARD
                        self.num_players = 3
                        self.reset_game_data()
                    elif event.key == pygame.K_y:
                        self.state = GameState.BOARD
                        self.num_players = 4
                        self.reset_game_data()
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS: # Plus key
                        self.state = GameState.EXPANSION_MENU
                        self.expansion_code = ""
                        self.expansion_message = ""
                        
                elif event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 0: # A / Cross (1P)
                         self.state = GameState.BOARD
                         self.num_players = 1
                         self.reset_game_data()
                    elif event.button == 1: # B / Circle (2P)
                         self.state = GameState.BOARD
                         self.num_players = 2
                         self.reset_game_data()
                    # Map X and Y if controller allows, typically X=2, Y=3
                    elif event.button == 2: # X / Square (3P)
                         self.state = GameState.BOARD
                         self.num_players = 3
                         self.reset_game_data()
                    elif event.button == 3: # Y / Triangle (4P)
                         self.state = GameState.BOARD
                         self.num_players = 4
                         self.reset_game_data()
                    elif event.button == 9 or event.button == 7: # Start/Options usually around 9 or 7
                         self.state = GameState.EXPANSION_MENU
                         self.expansion_code = ""
                         self.expansion_message = ""

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.state = GameState.BOARD
                    self.num_players = 1
                    self.reset_game_data()
            
            elif self.state == GameState.EXPANSION_MENU:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_b:
                        self.state = GameState.TITLE
                    
                    # Number input
                    if event.unicode.isdigit():
                        if len(self.expansion_code) < 12:
                             self.expansion_code += event.unicode
                    elif event.key == pygame.K_BACKSPACE:
                        self.expansion_code = self.expansion_code[:-1]
                    elif event.key == pygame.K_RETURN:
                         self.check_expansion_code()
                         
                    # Navigation
                    if event.key == pygame.K_LEFT:
                        self.keypad_selected_index = (self.keypad_selected_index - 1) % 12
                    elif event.key == pygame.K_RIGHT:
                        self.keypad_selected_index = (self.keypad_selected_index + 1) % 12
                    elif event.key == pygame.K_UP:
                        self.keypad_selected_index = (self.keypad_selected_index - 3) % 12
                    elif event.key == pygame.K_DOWN:
                        self.keypad_selected_index = (self.keypad_selected_index + 3) % 12
                    elif event.key == pygame.K_SPACE:
                        self.handle_keypad_press()
                    
                    # Paste Support (Ctrl+V / Cmd+V)
                    elif event.key == pygame.K_v and (event.mod & pygame.KMOD_CTRL or event.mod & pygame.KMOD_META):
                        try:
                            # Try to get text from clipboard
                            content = pygame.scrap.get(pygame.SCRAP_TEXT)
                            if content:
                                # Content might be bytes
                                if isinstance(content, bytes):
                                    text = content.decode('utf-8')
                                else:
                                    text = str(content)
                                
                                # Filter for digits only (since code is numerical)
                                digits = "".join([c for c in text if c.isdigit()])
                                
                                # Append to code, respecting limit
                                self.expansion_code = (self.expansion_code + digits)[:12]
                        except Exception as e:
                            print(f"Paste error: {e}")

                elif event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 1: # B / Circle - Back
                         self.state = GameState.TITLE
                    elif event.button == 0: # A / Cross - Select
                         self.handle_keypad_press()
                         
                # Joyhat/Axis for navigation (simple D-pad support)
                elif event.type == pygame.JOYHATMOTION:
                    hat = event.value
                    if hat[0] == -1: # Left
                         self.keypad_selected_index = (self.keypad_selected_index - 1) % 12
                    elif hat[0] == 1: # Right
                         self.keypad_selected_index = (self.keypad_selected_index + 1) % 12
                    elif hat[1] == 1: # Up
                         self.keypad_selected_index = (self.keypad_selected_index - 3) % 12
                    elif hat[1] == -1: # Down
                         self.keypad_selected_index = (self.keypad_selected_index + 3) % 12
                
                # Joystick Axis Navigation
                elif event.type == pygame.JOYAXISMOTION:
                    if self.nav_cooldown == 0:
                        # Axis 0: Left/Right, Axis 1: Up/Down
                        if event.axis == 0:
                            if event.value < -0.5:
                                self.keypad_selected_index = (self.keypad_selected_index - 1) % 12
                                self.nav_cooldown = 15
                            elif event.value > 0.5:
                                self.keypad_selected_index = (self.keypad_selected_index + 1) % 12
                                self.nav_cooldown = 15
                        elif event.axis == 1:
                            if event.value < -0.5:
                                self.keypad_selected_index = (self.keypad_selected_index - 3) % 12
                                self.nav_cooldown = 15
                            elif event.value > 0.5:
                                self.keypad_selected_index = (self.keypad_selected_index + 3) % 12
                                self.nav_cooldown = 15

            elif self.state == GameState.BOARD:
                # Trigger Boss Fight if player has 14+ stars
                if self.stars[self.turn] >= 14:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                         self.start_boss_fight()
                    elif event.type == pygame.JOYBUTTONDOWN and event.button == 0:
                         self.start_boss_fight()
                    return

                if event.type == pygame.KEYDOWN:
                    if (event.key == pygame.K_SPACE or event.key == pygame.K_a):
                        if not self.rolling_dice:
                            self.start_dice_roll()
                        elif not self.dice_stopped:
                            self.stop_dice_roll()
                            
                elif event.type == pygame.JOYBUTTONDOWN:
                    # Button 0 is usually 'A' or 'X'
                    if event.button == 0:
                        if not self.rolling_dice:
                            self.start_dice_roll()
                        elif not self.dice_stopped:
                            self.stop_dice_roll()
                            
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.dice_rect.collidepoint(event.pos):
                        if not self.rolling_dice:
                            self.start_dice_roll()
                        elif not self.dice_stopped:
                            self.stop_dice_roll()
        # Continuous input for minigame
        if self.state == GameState.MINIGAME and self.current_minigame:
            # Re-fetch input for minigame loop
            keys = pygame.key.get_pressed()
            active_joystick = next(iter(self.joysticks.values())) if self.joysticks else None
            self.current_minigame.handle_input(keys, active_joystick)

    def handle_keypad_press(self):
        char = self.keypad_grid[self.keypad_selected_index]
        if char.isdigit():
            if len(self.expansion_code) < 12:
                self.expansion_code += char
        elif char == 'CLR':
            self.expansion_code = ""
        elif char == 'ENT':
            self.check_expansion_code()
            
    def check_expansion_code(self):
        # Code: 56373849367
        if self.expansion_code == "56373849367":
            self.expansion_enabled = True
            self.expansion_message = "EXPANSION PACK ACTIVATED!"
            self.save_expansion_config()
        else:
            self.expansion_message = "INVALID CODE"
        self.expansion_message_timer = 120 # 2 seconds

    def stop_dice_roll(self):
        self.dice_stopped = True
        self.dice_jump_timer = 0
        
        # Continuous input for minigame
        # Not needed here really, only updated in handle_input
        pass

    def reset_game_data(self):
        self.dice_value = 0
        self.dice_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
        self.stars = [0, 0, 0, 0]
        self.turn = 0
        self.rolling_dice = False
        self.dice_stopped = False
        self.dice_jump_timer = 0

    def start_boss_fight(self):
        self.state = GameState.MINIGAME
        self.current_minigame = BossFightMinigame(self.screen, self.font, self.turn + 1)

    def start_dice_roll(self):
        self.rolling_dice = True
        self.dice_timer = 0 # Used for animation frame counter now
        self.dice_stopped = False
        self.dice_jump_timer = 0
        
    def update(self):
        # Update navigation cooldown
        if hasattr(self, 'nav_cooldown') and self.nav_cooldown > 0:
            self.nav_cooldown -= 1
            
        if self.state == GameState.SPLASH:
            self.splash_timer += 1
            if self.splash_timer > self.splash_duration:
                 self.state = GameState.TITLE
        
        elif self.state == GameState.EXPANSION_MENU:
            if self.expansion_message_timer > 0:
                self.expansion_message_timer -= 1
                if self.expansion_message_timer == 0 and self.expansion_enabled:
                    self.state = GameState.TITLE

        elif self.state == GameState.BOARD:
            if self.rolling_dice:
                if not self.dice_stopped:
                    # Animate dice rolling rapidly
                    self.dice_timer += 1
                    if self.dice_timer % 5 == 0: # Change face every 5 frames
                        max_val = 9 if self.expansion_enabled else 6
                        self.dice_value = random.randint(1, max_val)
                        
                    # Check for stop input
                    keys = pygame.key.get_pressed()
                    stop_pressed = keys[pygame.K_SPACE] or keys[pygame.K_a] # Keyboard
                    
                    # Controller input
                    if self.joysticks:
                        for joy in self.joysticks.values():
                            if joy.get_button(0): # A button
                                stop_pressed = True
                                break
                    
                    # Mouse input is handled in handle_input via flag if needed, but easier to check here?
                    # Actually handle_input sets flags usually. Let's rely on handle_input setting a flag or calling a method?
                    # The current design calls start_dice_roll on press. We need a "stop_dice_roll" action.
                    # Let's modify handle_input to handle the stop.
                    pass
                else:
                    # Dice Jump Animation
                    self.dice_jump_timer += 1
                    if self.dice_jump_timer > 30: # Animation done
                        self.rolling_dice = False
                        self.dice_stopped = False
                        # Start Minigame
                        self.state = GameState.MINIGAME
                        
                        if self.dice_value == 1:
                            self.current_minigame = BattleMinigame(self.screen, self.font, self.turn + 1)
                        elif self.dice_value == 2:
                            self.current_minigame = RacingMinigame(self.screen, self.font, self.turn + 1)
                        elif self.dice_value == 3:
                            self.current_minigame = PongMinigame(self.screen, self.font, self.turn + 1)
                        elif self.dice_value == 4:
                            self.current_minigame = DodgeballMinigame(self.screen, self.font, self.turn + 1)
                        elif self.dice_value == 5:
                            self.current_minigame = TargetMinigame(self.screen, self.font, self.turn + 1)
                        elif self.dice_value == 6:
                            self.current_minigame = CoinMinigame(self.screen, self.font, self.turn + 1)
                        # Expansion Games
                        elif self.dice_value == 7:
                            self.current_minigame = SnakeMinigame(self.screen, self.font, self.turn + 1)
                        elif self.dice_value == 8:
                            self.current_minigame = SpaceShooterMinigame(self.screen, self.font, self.turn + 1)
                        elif self.dice_value == 9:
                            self.current_minigame = PacmanMinigame(self.screen, self.font, self.turn + 1)

        
        elif self.state == GameState.MINIGAME:
            if self.current_minigame:
                result = self.current_minigame.update()
                if result:
                    # Boss Win (Game Over)
                    if "DEFEATED THE BOSS" in result:
                        self.winner = f"PLAYER {self.turn + 1} WINS THE GAME!"
                        self.state = GameState.GAME_OVER
                        return
                    
                    # Boss Loss
                    if "BOSS WINS" in result:
                        # Switch turn but don't reset stars, next player gets a chance if they have 14+ stars
                        if self.num_players > 1:
                            self.turn = (self.turn + 1) % self.num_players
                        
                        self.state = GameState.BOARD
                        self.current_minigame = None
                        self.dice_value = 0
                        return

                    # Mini-game Win logic
                    if "Player 1 Wins!" in result or "You Survived!" in result or "Time's Up!" in result or "Win" in result:
                        # Check specific win conditions per game if needed, but simplified:
                        # Assume standard win text implies player victory
                        if "Computer" not in result and "LOSE" not in result:
                             self.stars[self.turn] += 1

                    # Mini-game end
                    if self.num_players > 1:
                        self.turn = (self.turn + 1) % self.num_players # Switch turn
                    
                    self.state = GameState.BOARD
                    self.current_minigame = None
                    self.dice_value = 0

    def draw(self):
        self.screen.fill(BLACK)
        
        if self.state == GameState.SPLASH:
            self.draw_splash()
        elif self.state == GameState.TITLE:
            self.draw_title()
        elif self.state == GameState.EXPANSION_MENU:
            self.draw_expansion_menu()
        elif self.state == GameState.BOARD:
            self.draw_board()
        elif self.state == GameState.MINIGAME:
            if self.current_minigame:
                self.current_minigame.draw()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
            
        pygame.display.flip()

    def draw_expansion_menu(self):
        self.screen.fill(BLACK)
        
        # Title
        title = self.font.render("ENTER EXPANSION CODE", True, YELLOW)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        # Code Display (Masked or Clear - user said "type in expansion code", usually visible)
        # Using simple box
        pygame.draw.rect(self.screen, WHITE, (SCREEN_WIDTH//2 - 200, 150, 400, 50), 2)
        code_text = self.font.render(self.expansion_code, True, WHITE)
        self.screen.blit(code_text, (SCREEN_WIDTH//2 - code_text.get_width()//2, 160))
        
        # Keypad Grid
        start_x = SCREEN_WIDTH//2 - 100
        start_y = 250
        cell_size = 60
        gap = 10
        
        for i, char in enumerate(self.keypad_grid):
            row = i // 3
            col = i % 3
            x = start_x + col * (cell_size + gap)
            y = start_y + row * (cell_size + gap)
            
            rect = pygame.Rect(x, y, cell_size, cell_size)
            
            # Highlight selected
            if i == self.keypad_selected_index:
                pygame.draw.rect(self.screen, YELLOW, rect)
                text_color = BLACK
            else:
                pygame.draw.rect(self.screen, BLUE, rect, 2)
                text_color = WHITE
                
            text = self.small_font.render(char, True, text_color)
            self.screen.blit(text, (x + cell_size//2 - text.get_width()//2, y + cell_size//2 - text.get_height()//2))
            
        # Message
        if self.expansion_message:
            color = GREEN if "ACTIVATED" in self.expansion_message else RED
            msg = self.small_font.render(self.expansion_message, True, color)
            self.screen.blit(msg, (SCREEN_WIDTH//2 - msg.get_width()//2, 500))
            
        # Instructions
        instr = self.tiny_font.render("Use D-Pad/Arrows to Move, A/Space to Select, B/Esc to Back", True, GREY if 'GREY' in globals() else (100,100,100))
        self.screen.blit(instr, (SCREEN_WIDTH//2 - instr.get_width()//2, SCREEN_HEIGHT - 30))

    def draw_game_over(self):
        self.screen.fill(BLUE)
        text = self.font.render(getattr(self, 'winner', "GAME OVER"), True, WHITE)
        self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2))
        
        sub = self.small_font.render("Press ESC to Exit", True, WHITE)
        self.screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, SCREEN_HEIGHT//2 + 100))
        
        # Handle input to exit
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            self.running = False

    def draw_splash(self):
        self.screen.fill(WHITE)
        
        # Determine alpha for fade out
        # Fade out in last 60 frames
        alpha = 255
        if self.splash_timer > self.splash_duration - 60:
            alpha = int(255 * ((self.splash_duration - self.splash_timer) / 60))
        
        if self.splash_image:
             self.splash_image.set_alpha(alpha)
             self.screen.blit(self.splash_image, (SCREEN_WIDTH//2 - self.splash_image.get_width()//2, SCREEN_HEIGHT//2 - 180))
        
        text_surf = self.font.render("Team Banana Labs Studios", True, BLACK)
        text_surf.set_alpha(alpha)
        self.screen.blit(text_surf, (SCREEN_WIDTH//2 - text_surf.get_width()//2, SCREEN_HEIGHT//2 + 150))
        
        # Overlay for fade effect
        if alpha < 255:
             s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
             s.set_alpha(255 - alpha)
             s.fill(BLACK) # Fade to whatever color title starts with (Purple/Black)
             self.screen.blit(s, (0,0))

    def draw_title(self):
        self.screen.fill(PURPLE)
        
        # Simple decorative elements
        pygame.draw.circle(self.screen, YELLOW, (100, 100), 50)
        pygame.draw.circle(self.screen, RED, (SCREEN_WIDTH-100, SCREEN_HEIGHT-100), 80)
        
        title_text = self.font.render("Battle Street 2", True, WHITE)
        subtitle_text = self.font.render("Party Edition", True, GREEN)
        
        # Shadow effect
        title_shadow = self.font.render("Battle Street 2", True, BLACK)
        self.screen.blit(title_shadow, (SCREEN_WIDTH//2 - title_text.get_width()//2 + 4, 154))
        
        self.screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 150))
        self.screen.blit(subtitle_text, (SCREEN_WIDTH//2 - subtitle_text.get_width()//2, 230))
        
        start_text = self.small_font.render("Press A / Space for 1 Player", True, WHITE)
        p2_text = self.small_font.render("Press B for 2 Players", True, YELLOW)
        p3_text = self.small_font.render("Press X for 3 Players", True, GREEN)
        p4_text = self.small_font.render("Press Y for 4 Players", True, PURPLE)
        
        self.screen.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, 380))
        self.screen.blit(p2_text, (SCREEN_WIDTH//2 - p2_text.get_width()//2, 420))
        self.screen.blit(p3_text, (SCREEN_WIDTH//2 - p3_text.get_width()//2, 460))
        self.screen.blit(p4_text, (SCREEN_WIDTH//2 - p4_text.get_width()//2, 500))
        
        if self.expansion_enabled:
            exp_text = self.tiny_font.render("EXPANSION PACK ENABLED", True, GOLD if 'GOLD' in globals() else (255, 215, 0))
            self.screen.blit(exp_text, (SCREEN_WIDTH - exp_text.get_width() - 10, 10))
        
        if self.joysticks:
            joy_name = next(iter(self.joysticks.values())).get_name()
            joy_text = self.tiny_font.render(f"Controller: {joy_name}", True, BLUE)
            self.screen.blit(joy_text, (10, SCREEN_HEIGHT - 30))
        else:
            kb_text = self.tiny_font.render("No Controller Detected (Use Keyboard)", True, RED)
            self.screen.blit(kb_text, (10, SCREEN_HEIGHT - 30))
            
        controls_text = self.tiny_font.render("Controls: Arrows/WASD to Move, Space/Btn 0 to Action", True, WHITE)
        self.screen.blit(controls_text, (SCREEN_WIDTH - controls_text.get_width() - 10, SCREEN_HEIGHT - 30))
        
        expansion_hint = self.tiny_font.render("Press + / Start for Expansion Menu", True, WHITE)
        self.screen.blit(expansion_hint, (SCREEN_WIDTH//2 - expansion_hint.get_width()//2, SCREEN_HEIGHT - 30))

    def draw_board(self):
        self.screen.fill((20, 20, 40))
        
        # Header
        colors = [BLUE, RED, GREEN, YELLOW]
        turn_text = self.font.render(f"Player {self.turn + 1}'s Turn", True, colors[self.turn])
        self.screen.blit(turn_text, (SCREEN_WIDTH//2 - turn_text.get_width()//2, 30))
        
        mode_text = self.tiny_font.render(f"Current Mode: {self.num_players} Player(s)", True, WHITE)
        self.screen.blit(mode_text, (10, 10))
        
        # Stars
        colors = [BLUE, RED, GREEN, YELLOW]
        p_star_text = self.small_font.render(f"P{self.turn+1} Stars: {self.stars[self.turn]}/14", True, colors[self.turn])
        self.screen.blit(p_star_text, (50, 50))
        
        # Show all players stars small in corners or list
        if self.num_players > 1:
            for i in range(self.num_players):
                t = self.tiny_font.render(f"P{i+1}: {self.stars[i]}", True, colors[i])
                self.screen.blit(t, (SCREEN_WIDTH - 100, 30 + i*20))
        
        # Boss Ready?
        if self.stars[self.turn] >= 14:
            boss_text = self.font.render("BOSS UNLOCKED!", True, RED)
            sub_text = self.small_font.render("Press Space/A to Fight!", True, WHITE)
            
            blink_alpha = abs(pygame.time.get_ticks() % 1000 - 500) // 2
            boss_text.set_alpha(blink_alpha)
            
            self.screen.blit(boss_text, (SCREEN_WIDTH//2 - boss_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
            self.screen.blit(sub_text, (SCREEN_WIDTH//2 - sub_text.get_width()//2, SCREEN_HEIGHT//2 + 50))
            return

        if not self.rolling_dice and self.dice_value == 0:
            instruction = self.small_font.render("Roll the Dice!", True, GREEN)
            self.screen.blit(instruction, (SCREEN_WIDTH//2 - instruction.get_width()//2, 500))
        
        # Draw Dice
        # Use self.dice_rect which is now initialized in __init__
        dice_y_offset = 0
        if self.dice_stopped and self.rolling_dice:
            # Simple jump animation: up then down
            if self.dice_jump_timer < 15:
                dice_y_offset = -self.dice_jump_timer * 2
            else:
                dice_y_offset = -(30 - self.dice_jump_timer) * 2
        
        draw_rect = self.dice_rect.copy()
        draw_rect.y += dice_y_offset
        
        pygame.draw.rect(self.screen, WHITE, draw_rect, border_radius=10)
        pygame.draw.rect(self.screen, BLACK, draw_rect, 4, border_radius=10)
        
        if self.dice_value > 0:
            # Draw dots based on number
            color = BLACK
            cx, cy = draw_rect.centerx, draw_rect.centery
            
            # Dice logic for 1-6 is standard
            if self.dice_value <= 6:
                if self.dice_value in [1, 3, 5]:
                    pygame.draw.circle(self.screen, color, (cx, cy), 10)
                if self.dice_value in [2, 3, 4, 5, 6]:
                    pygame.draw.circle(self.screen, color, (cx - 25, cy - 25), 10)
                    pygame.draw.circle(self.screen, color, (cx + 25, cy + 25), 10)
                if self.dice_value in [4, 5, 6]:
                    pygame.draw.circle(self.screen, color, (cx + 25, cy - 25), 10)
                    pygame.draw.circle(self.screen, color, (cx - 25, cy + 25), 10)
                if self.dice_value == 6:
                    pygame.draw.circle(self.screen, color, (cx - 25, cy), 10)
                    pygame.draw.circle(self.screen, color, (cx + 25, cy), 10)
            else:
                # Custom numbers for 7, 8 etc
                text_surf = self.font.render(str(self.dice_value), True, BLACK)
                self.screen.blit(text_surf, (cx - text_surf.get_width()//2, cy - text_surf.get_height()//2))
            
            # Show which game
            game_name = ""
            if self.dice_value == 1: game_name = "BATTLE ARENA"
            elif self.dice_value == 2: game_name = "RACING"
            elif self.dice_value == 3: game_name = "PONG"
            elif self.dice_value == 4: game_name = "DODGEBALL"
            elif self.dice_value == 5: game_name = "TARGET PRACTICE"
            elif self.dice_value == 6: game_name = "COIN COLLECTOR"
            elif self.dice_value == 7: game_name = "SNAKE"
            elif self.dice_value == 8: game_name = "SPACE SHOOTER"
            
            name_text = self.small_font.render(game_name, True, YELLOW)
            self.screen.blit(name_text, (SCREEN_WIDTH//2 - name_text.get_width()//2, SCREEN_HEIGHT//2 + 80))

        # Draw Player Characters at bottom
        for i in range(self.num_players):
            p_color = colors[i % 4]
            # Highlight current turn player
            if i == self.turn:
                # If jumping to hit dice
                if self.dice_stopped and self.rolling_dice:
                     # Calculate jump pos
                     p_y = SCREEN_HEIGHT - 100 + dice_y_offset
                     p_x = SCREEN_WIDTH//2
                else:
                     p_y = SCREEN_HEIGHT - 100
                     p_x = 100 + i * 150
            else:
                p_y = SCREEN_HEIGHT - 100
                p_x = 100 + i * 150
                
            pygame.draw.rect(self.screen, p_color, (p_x, p_y, 40, 60))
            # Eyes
            pygame.draw.rect(self.screen, WHITE, (p_x + 5, p_y + 10, 10, 10))
            pygame.draw.rect(self.screen, WHITE, (p_x + 25, p_y + 10, 10, 10))
            
            # Indicator for current turn if not jumping
            if i == self.turn and not (self.dice_stopped and self.rolling_dice):
                pygame.draw.polygon(self.screen, WHITE, [(p_x + 20, p_y - 20), (p_x + 10, p_y - 40), (p_x + 30, p_y - 40)])

    def run(self):
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()

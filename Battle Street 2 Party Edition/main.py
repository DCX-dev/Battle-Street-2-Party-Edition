import pygame
import sys
import random
import os
from minigames import BattleMinigame, RacingMinigame, PongMinigame, DodgeballMinigame, TargetMinigame, CoinMinigame, BossFightMinigame

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

class GameState:
    SPLASH = "SPLASH"
    TITLE = "TITLE"
    BOARD = "BOARD"
    MINIGAME = "MINIGAME"
    GAME_OVER = "GAME_OVER"

class Game:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        
        # Update dimensions to actual fullscreen size
        global SCREEN_WIDTH, SCREEN_HEIGHT
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        SCREEN_WIDTH, SCREEN_HEIGHT = self.screen.get_size()
        
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
        self.dice_timer = 0
        self.dice_rect = pygame.Rect(SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT//2 - 50, 100, 100)
        
        # Minigame
        self.current_minigame = None
        
        # Multiplayer & Stats
        self.num_players = 1 # Default 1 player
        self.turn = 0 # 0 = P1, 1 = P2, 2 = P3, 3 = P4
        self.stars = [0, 0, 0, 0] # Up to 4 players
        
        # Splash Data
        self.splash_timer = 0
        self.splash_duration = 180 # 3 seconds
        self.splash_alpha = 255
        self.splash_image = self.load_studio_logo()

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

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.state = GameState.BOARD
                    self.num_players = 1
                    self.reset_game_data()
            
            elif self.state == GameState.BOARD:
                # Trigger Boss Fight if player has 14+ stars
                if self.stars[self.turn] >= 14:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                         self.start_boss_fight()
                    elif event.type == pygame.JOYBUTTONDOWN and event.button == 0:
                         self.start_boss_fight()
                    return

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not self.rolling_dice:
                        self.start_dice_roll()
                elif event.type == pygame.JOYBUTTONDOWN:
                    # Button 0 is usually 'A' or 'X'
                    if event.button == 0 and not self.rolling_dice:
                        self.start_dice_roll()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.rolling_dice and self.dice_rect.collidepoint(event.pos):
                        self.start_dice_roll()
        
        # Continuous input for minigame
        if self.state == GameState.MINIGAME and self.current_minigame:
            self.current_minigame.handle_input(keys, active_joystick)

    def reset_game_data(self):
        self.dice_value = 0
        self.dice_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
        self.stars = [0, 0, 0, 0]
        self.turn = 0

    def start_boss_fight(self):
        self.state = GameState.MINIGAME
        self.current_minigame = BossFightMinigame(self.screen, self.font)

    def start_dice_roll(self):
        self.rolling_dice = True
        self.dice_timer = 60 # Frames to roll
        
    def update(self):
        if self.state == GameState.SPLASH:
            self.splash_timer += 1
            if self.splash_timer > self.splash_duration:
                 self.state = GameState.TITLE
        
        elif self.state == GameState.BOARD:
            if self.rolling_dice:
                self.dice_value = random.randint(1, 6)
                self.dice_timer -= 1
                if self.dice_timer <= 0:
                    self.rolling_dice = False
                    # Start Minigame based on Dice Value
                    self.state = GameState.MINIGAME
                    
                    if self.dice_value == 1:
                        self.current_minigame = BattleMinigame(self.screen, self.font)
                    elif self.dice_value == 2:
                        self.current_minigame = RacingMinigame(self.screen, self.font)
                    elif self.dice_value == 3:
                        self.current_minigame = PongMinigame(self.screen, self.font)
                    elif self.dice_value == 4:
                        self.current_minigame = DodgeballMinigame(self.screen, self.font)
                    elif self.dice_value == 5:
                        self.current_minigame = TargetMinigame(self.screen, self.font)
                    elif self.dice_value == 6:
                        self.current_minigame = CoinMinigame(self.screen, self.font)

        
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
        elif self.state == GameState.BOARD:
            self.draw_board()
        elif self.state == GameState.MINIGAME:
            if self.current_minigame:
                self.current_minigame.draw()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
            
        pygame.display.flip()

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
        
        blink_speed = 30
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            start_text = self.small_font.render("Press A / Space for 1 Player", True, WHITE)
            p2_text = self.small_font.render("Press B for 2 Players", True, YELLOW)
            p3_text = self.small_font.render("Press X for 3 Players", True, GREEN)
            p4_text = self.small_font.render("Press Y for 4 Players", True, PURPLE)
            
            self.screen.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, 380))
            self.screen.blit(p2_text, (SCREEN_WIDTH//2 - p2_text.get_width()//2, 420))
            self.screen.blit(p3_text, (SCREEN_WIDTH//2 - p3_text.get_width()//2, 460))
            self.screen.blit(p4_text, (SCREEN_WIDTH//2 - p4_text.get_width()//2, 500))
        
        if self.joysticks:
            joy_name = next(iter(self.joysticks.values())).get_name()
            joy_text = self.tiny_font.render(f"Controller: {joy_name}", True, BLUE)
            self.screen.blit(joy_text, (10, SCREEN_HEIGHT - 30))
        else:
            kb_text = self.tiny_font.render("No Controller Detected (Use Keyboard)", True, RED)
            self.screen.blit(kb_text, (10, SCREEN_HEIGHT - 30))
            
        controls_text = self.tiny_font.render("Controls: Arrows/WASD to Move, Space/Btn 0 to Action", True, WHITE)
        self.screen.blit(controls_text, (SCREEN_WIDTH - controls_text.get_width() - 10, SCREEN_HEIGHT - 30))

    def draw_board(self):
        self.screen.fill((20, 20, 40))
        
        # Header
        colors = [BLUE, RED, GREEN, YELLOW]
        turn_text = self.font.render(f"Player {self.turn + 1}'s Turn", True, colors[self.turn])
        self.screen.blit(turn_text, (SCREEN_WIDTH//2 - turn_text.get_width()//2, 30))
        
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
        pygame.draw.rect(self.screen, WHITE, self.dice_rect, border_radius=10)
        pygame.draw.rect(self.screen, BLACK, self.dice_rect, 4, border_radius=10)
        
        if self.dice_value > 0:
            # Draw dots based on number
            color = BLACK
            cx, cy = self.dice_rect.centerx, self.dice_rect.centery
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
            
            # Show which game
            game_name = ""
            if self.dice_value == 1: game_name = "BATTLE ARENA"
            elif self.dice_value == 2: game_name = "RACING"
            elif self.dice_value == 3: game_name = "PONG"
            elif self.dice_value == 4: game_name = "DODGEBALL"
            elif self.dice_value == 5: game_name = "TARGET PRACTICE"
            elif self.dice_value == 6: game_name = "COIN COLLECTOR"
            
            name_text = self.small_font.render(game_name, True, YELLOW)
            self.screen.blit(name_text, (SCREEN_WIDTH//2 - name_text.get_width()//2, SCREEN_HEIGHT//2 + 80))

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

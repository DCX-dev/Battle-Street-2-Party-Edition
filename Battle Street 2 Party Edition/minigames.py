import pygame
import random

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
GREY = (100, 100, 100)

class BossFightMinigame:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.reset()
        
    def reset(self):
        self.player_rect = pygame.Rect(100, SCREEN_HEIGHT//2, 50, 50)
        self.player_color = BLUE
        self.player_hp = 100
        self.player_speed = 5
        
        self.boss_rect = pygame.Rect(SCREEN_WIDTH - 150, SCREEN_HEIGHT//2 - 75, 150, 150)
        self.boss_color = (100, 0, 0) # Dark Red
        self.boss_hp = 500
        self.boss_state = "IDLE"
        self.boss_timer = 0
        
        self.projectiles = [] # Fireballs / Rockets
        self.player_projectiles = [] # Player's fireballs
        self.player_attack_cooldown = 0
        self.winner = None
        self.game_over_timer = 0
        
    def handle_input(self, keys, joystick=None):
        if self.winner: return
        
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]: dx = -1
        if keys[pygame.K_RIGHT]: dx = 1
        if keys[pygame.K_UP]: dy = -1
        if keys[pygame.K_DOWN]: dy = 1
        
        if joystick:
            ax = joystick.get_axis(0)
            ay = joystick.get_axis(1)
            if abs(ax) > 0.1: dx = ax
            if abs(ay) > 0.1: dy = ay
            
        self.player_rect.x += dx * self.player_speed
        self.player_rect.y += dy * self.player_speed
        self.player_rect.clamp_ip(self.screen.get_rect())
        
        # Attack
        attack = False
        if keys[pygame.K_SPACE]: attack = True
        if joystick and joystick.get_button(0): attack = True
        
        if attack and self.player_attack_cooldown == 0:
            # Check distance to boss for Melee vs Ranged
            dist = ((self.player_rect.centerx - self.boss_rect.centerx)**2 + (self.player_rect.centery - self.boss_rect.centery)**2)**0.5
            
            if dist < 150: # Close range: Fist
                attack_rect = pygame.Rect(self.player_rect.right, self.player_rect.y, 60, 50)
                if attack_rect.colliderect(self.boss_rect):
                    self.boss_hp -= 5 # Fist damage
                self.player_attack_cooldown = 20
            else: # Long range: Fireball
                self.player_projectiles.append(pygame.Rect(self.player_rect.right, self.player_rect.centery - 10, 20, 20))
                self.player_attack_cooldown = 30

    def update(self):
        if self.winner:
            self.game_over_timer += 1
            return self.winner if self.game_over_timer > 180 else None
            
        if self.player_attack_cooldown > 0:
            self.player_attack_cooldown -= 1
            
        # Boss AI
        self.boss_timer += 1
        
        if self.boss_state == "IDLE":
            # Drift up and down
            self.boss_rect.y += random.choice([-2, 2])
            self.boss_rect.clamp_ip(self.screen.get_rect())
            
            if self.boss_timer > 60:
                self.boss_state = random.choice(["FIREBALL", "FIST", "ROCKET"])
                self.boss_timer = 0
                
        elif self.boss_state == "FIREBALL":
            if self.boss_timer % 20 == 0: # Shoot every 20 frames
                # Create fireball
                self.projectiles.append({
                    "rect": pygame.Rect(self.boss_rect.left, self.boss_rect.centery, 30, 30),
                    "dx": -8,
                    "dy": random.randint(-3, 3),
                    "type": "FIREBALL"
                })
            if self.boss_timer > 100:
                self.boss_state = "IDLE"
                self.boss_timer = 0
                
        elif self.boss_state == "FIST":
            # Charge forward
            self.boss_rect.x -= 10
            if self.boss_rect.x < 100:
                self.boss_state = "RETREAT"
        
        elif self.boss_state == "RETREAT":
            self.boss_rect.x += 5
            if self.boss_rect.x > SCREEN_WIDTH - 200:
                self.boss_state = "IDLE"
                self.boss_timer = 0
                
        elif self.boss_state == "ROCKET":
            if self.boss_timer == 30: # Shoot one big rocket
                self.projectiles.append({
                    "rect": pygame.Rect(self.boss_rect.left, self.boss_rect.centery, 50, 20),
                    "dx": -5,
                    "dy": 0,
                    "type": "ROCKET"
                })
            if self.boss_timer > 80:
                self.boss_state = "IDLE"
                self.boss_timer = 0
        
        # Projectiles Logic
        for p in self.projectiles[:]:
            p["rect"].x += p["dx"]
            p["rect"].y += p["dy"]
            
            # Homing logic for rocket
            if p["type"] == "ROCKET":
                if p["rect"].y < self.player_rect.y: p["dy"] = 2
                elif p["rect"].y > self.player_rect.y: p["dy"] = -2
            
            if p["rect"].colliderect(self.player_rect):
                damage = 15 if p["type"] == "ROCKET" else 10
                self.player_hp -= damage
                self.projectiles.remove(p)
            elif p["rect"].right < 0:
                self.projectiles.remove(p)
        
        # Player Projectiles Logic
        for pp in self.player_projectiles[:]:
            pp.x += 10 # Move right
            if pp.colliderect(self.boss_rect):
                self.boss_hp -= 2 # Fireball damage
                self.player_projectiles.remove(pp)
            elif pp.x > SCREEN_WIDTH:
                self.player_projectiles.remove(pp)
                
        # Boss Collision
        if self.boss_rect.colliderect(self.player_rect):
            self.player_hp -= 1
            
        # Win/Loss
        if self.player_hp <= 0:
            self.winner = "BOSS WINS! YOU LOSE!"
        elif self.boss_hp <= 0:
            self.winner = "YOU DEFEATED THE BOSS!"
            
        return None

    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw Boss
        pygame.draw.rect(self.screen, self.boss_color, self.boss_rect)
        # Draw Boss Eyes
        pygame.draw.rect(self.screen, YELLOW, (self.boss_rect.x + 20, self.boss_rect.y + 30, 30, 30))
        
        # Draw Player
        pygame.draw.rect(self.screen, self.player_color, self.player_rect)
        
        # Draw Projectiles
        for p in self.projectiles:
            color = ORANGE if p["type"] == "FIREBALL" else GREEN
            pygame.draw.rect(self.screen, color, p["rect"])
            
        # Draw Player Projectiles
        for pp in self.player_projectiles:
            pygame.draw.circle(self.screen, (0, 255, 255), pp.center, 10)
            
        # Health Bars
        # Player
        pygame.draw.rect(self.screen, RED, (50, 50, 200, 20))
        pygame.draw.rect(self.screen, GREEN, (50, 50, 200 * (max(0, self.player_hp)/100), 20))
        
        # Boss
        pygame.draw.rect(self.screen, RED, (SCREEN_WIDTH - 450, 50, 400, 30))
        pygame.draw.rect(self.screen, YELLOW, (SCREEN_WIDTH - 450, 50, 400 * (max(0, self.boss_hp)/500), 30))
        
        if self.winner:
            win_text = self.font.render(self.winner, True, WHITE)
            self.screen.blit(win_text, (SCREEN_WIDTH//2 - win_text.get_width()//2, SCREEN_HEIGHT//2))

class BattleMinigame:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.reset()
        
    def reset(self):
        # Player 1 (Blue)
        self.p1_rect = pygame.Rect(100, 300, 50, 50)
        self.p1_color = BLUE
        self.p1_health = 100
        self.p1_speed = 5
        
        # Player 2 / AI (Red)
        self.p2_rect = pygame.Rect(650, 300, 50, 50)
        self.p2_color = RED
        self.p2_health = 100
        self.p2_speed = 3 # AI is slower
        
        self.winner = None
        self.game_over_timer = 0
        
        # Attack cooldowns
        self.p1_attack_cooldown = 0
        self.p2_attack_cooldown = 0
        
    def handle_input(self, keys, joystick=None):
        if self.winner:
            return

        # Player 1 Movement
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]: dx = -1
        if keys[pygame.K_RIGHT]: dx = 1
        if keys[pygame.K_UP]: dy = -1
        if keys[pygame.K_DOWN]: dy = 1
        
        # Joystick support
        if joystick:
            # Axis 0 is usually Left/Right, Axis 1 is Up/Down
            axis_x = joystick.get_axis(0)
            axis_y = joystick.get_axis(1)
            if abs(axis_x) > 0.1: dx = axis_x
            if abs(axis_y) > 0.1: dy = axis_y
            
        self.p1_rect.x += dx * self.p1_speed
        self.p1_rect.y += dy * self.p1_speed
        
        # Attack
        attack = False
        if keys[pygame.K_SPACE]: attack = True
        if joystick and joystick.get_button(0): attack = True
        
        if attack and self.p1_attack_cooldown == 0:
            self.attack(self.p1_rect, self.p2_rect, is_p1=True)

        # Boundary checks
        self.p1_rect.clamp_ip(self.screen.get_rect())

    def ai_logic(self):
        if self.winner:
            return

        # Simple AI: Move towards player
        if self.p2_rect.x > self.p1_rect.x:
            self.p2_rect.x -= self.p2_speed
        elif self.p2_rect.x < self.p1_rect.x:
            self.p2_rect.x += self.p2_speed
            
        if self.p2_rect.y > self.p1_rect.y:
            self.p2_rect.y -= self.p2_speed
        elif self.p2_rect.y < self.p1_rect.y:
            self.p2_rect.y += self.p2_speed
            
        # AI Attack logic
        dist = ((self.p1_rect.centerx - self.p2_rect.centerx)**2 + (self.p1_rect.centery - self.p2_rect.centery)**2)**0.5
        if dist < 60 and self.p2_attack_cooldown == 0:
             self.attack(self.p2_rect, self.p1_rect, is_p1=False)

    def attack(self, attacker_rect, target_rect, is_p1):
        # Check range
        dist = ((attacker_rect.centerx - target_rect.centerx)**2 + (attacker_rect.centery - target_rect.centery)**2)**0.5
        if dist < 70: # Hit range
            if is_p1:
                self.p2_health -= 10
                self.p1_attack_cooldown = 30
            else:
                self.p1_health -= 5 # AI does less damage
                self.p2_attack_cooldown = 60

    def update(self):
        if self.winner:
            self.game_over_timer += 1
            return self.winner if self.game_over_timer > 180 else None

        self.ai_logic()
        
        # Cooldowns
        if self.p1_attack_cooldown > 0: self.p1_attack_cooldown -= 1
        if self.p2_attack_cooldown > 0: self.p2_attack_cooldown -= 1
        
        # Check Win
        if self.p2_health <= 0:
            self.winner = "Player 1 Wins!"
        elif self.p1_health <= 0:
            self.winner = "Computer Wins!"
            
        return None

    def draw(self):
        self.screen.fill((50, 50, 50)) # Grey background arena
        
        # Draw Players
        pygame.draw.rect(self.screen, self.p1_color, self.p1_rect)
        pygame.draw.rect(self.screen, self.p2_color, self.p2_rect)
        
        # Draw Health Bars
        pygame.draw.rect(self.screen, RED, (50, 50, 200, 20))
        pygame.draw.rect(self.screen, GREEN, (50, 50, 200 * (self.p1_health/100), 20))
        
        pygame.draw.rect(self.screen, RED, (550, 50, 200, 20))
        pygame.draw.rect(self.screen, GREEN, (550, 50, 200 * (self.p2_health/100), 20))
        
        # Attack indicator
        if self.p1_attack_cooldown > 15:
            pygame.draw.circle(self.screen, WHITE, self.p1_rect.center, 40, 2)
            
        if self.winner:
            win_text = self.font.render(self.winner, True, WHITE)
            self.screen.blit(win_text, (SCREEN_WIDTH//2 - win_text.get_width()//2, SCREEN_HEIGHT//2))


class RacingMinigame:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.reset()
        
    def reset(self):
        self.p1_y = 400
        self.p2_y = 400
        self.p1_x = 200
        self.p2_x = 500
        self.finish_line_y = 50
        self.winner = None
        self.game_over_timer = 0
        
    def handle_input(self, keys, joystick=None):
        if self.winner: return
        
        # Mash button/key to move forward
        # We need a 'pressed this frame' check, but for simplicity, we'll just check rapid polling or use a cooldown
        # Ideally, main.py handles 'just pressed', but here we'll just add speed per frame if held, but slower
        # To make it mash-y, we'd need 'just_pressed' passed in. 
        # Let's make it "hold to move but slow, or mash to move fast".
        # For simplicity in this structure, let's just make it HOLD to run for now, or rely on main loop.
        
        # Actually, let's just make it speed based on holding for now to ensure it works easily
        speed = 5
        
        if keys[pygame.K_SPACE]:
            self.p1_y -= speed
        elif joystick and joystick.get_button(0):
            self.p1_y -= speed
            
    def update(self):
        if self.winner:
            self.game_over_timer += 1
            return self.winner if self.game_over_timer > 180 else None
            
        # AI Movement (random speed)
        self.p2_y -= random.randint(3, 6)
        
        if self.p1_y <= self.finish_line_y:
            self.winner = "Player 1 Wins!"
        elif self.p2_y <= self.finish_line_y:
            self.winner = "Computer Wins!"
            
        return None

    def draw(self):
        self.screen.fill((30, 100, 30)) # Grass
        
        # Track
        pygame.draw.rect(self.screen, (100, 100, 100), (150, 0, 500, SCREEN_HEIGHT))
        
        # Finish Line
        pygame.draw.rect(self.screen, WHITE, (150, self.finish_line_y, 500, 10))
        
        # Cars/Runners
        pygame.draw.rect(self.screen, BLUE, (self.p1_x, self.p1_y, 40, 60))
        pygame.draw.rect(self.screen, RED, (self.p2_x, self.p2_y, 40, 60))
        
        if self.winner:
            win_text = self.font.render(self.winner, True, WHITE)
            self.screen.blit(win_text, (SCREEN_WIDTH//2 - win_text.get_width()//2, SCREEN_HEIGHT//2))


class PongMinigame:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.reset()
        
    def reset(self):
        self.paddle_h = 80
        self.paddle_w = 15
        
        self.p1_y = SCREEN_HEIGHT//2 - self.paddle_h//2
        self.p2_y = SCREEN_HEIGHT//2 - self.paddle_h//2
        
        self.ball_x = SCREEN_WIDTH//2
        self.ball_y = SCREEN_HEIGHT//2
        self.ball_dx = 5 * random.choice([-1, 1])
        self.ball_dy = 5 * random.choice([-1, 1])
        
        self.winner = None
        self.game_over_timer = 0
        self.score_p1 = 0
        self.score_p2 = 0
        
    def handle_input(self, keys, joystick=None):
        if self.winner: return
        
        speed = 6
        if keys[pygame.K_UP]: self.p1_y -= speed
        if keys[pygame.K_DOWN]: self.p1_y += speed
        
        if joystick:
            axis = joystick.get_axis(1)
            if abs(axis) > 0.1:
                self.p1_y += axis * speed
                
        # Clamp
        self.p1_y = max(0, min(SCREEN_HEIGHT - self.paddle_h, self.p1_y))

    def update(self):
        if self.winner:
            self.game_over_timer += 1
            return self.winner if self.game_over_timer > 180 else None
            
        # AI
        if self.ball_y < self.p2_y + self.paddle_h//2:
            self.p2_y -= 4
        elif self.ball_y > self.p2_y + self.paddle_h//2:
            self.p2_y += 4
        self.p2_y = max(0, min(SCREEN_HEIGHT - self.paddle_h, self.p2_y))
        
        # Ball Movement
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy
        
        # Bounce top/bottom
        if self.ball_y <= 0 or self.ball_y >= SCREEN_HEIGHT:
            self.ball_dy *= -1
            
        # Paddles
        p1_rect = pygame.Rect(50, self.p1_y, self.paddle_w, self.paddle_h)
        p2_rect = pygame.Rect(SCREEN_WIDTH - 50 - self.paddle_w, self.p2_y, self.paddle_w, self.paddle_h)
        ball_rect = pygame.Rect(self.ball_x - 10, self.ball_y - 10, 20, 20)
        
        if ball_rect.colliderect(p1_rect):
            self.ball_dx = abs(self.ball_dx)
            self.ball_dx += 0.5 # Speed up
        if ball_rect.colliderect(p2_rect):
            self.ball_dx = -abs(self.ball_dx)
             # Speed up
             
        # Score
        if self.ball_x < 0:
            self.score_p2 += 1
            self.reset_ball()
        elif self.ball_x > SCREEN_WIDTH:
            self.score_p1 += 1
            self.reset_ball()
            
        if self.score_p1 >= 3:
            self.winner = "Player 1 Wins!"
        elif self.score_p2 >= 3:
            self.winner = "Computer Wins!"
            
        return None

    def reset_ball(self):
        self.ball_x = SCREEN_WIDTH//2
        self.ball_y = SCREEN_HEIGHT//2
        self.ball_dx = 5 * random.choice([-1, 1])
        self.ball_dy = 5 * random.choice([-1, 1])

    def draw(self):
        self.screen.fill(BLACK)
        pygame.draw.line(self.screen, WHITE, (SCREEN_WIDTH//2, 0), (SCREEN_WIDTH//2, SCREEN_HEIGHT), 2)
        
        # Paddles
        pygame.draw.rect(self.screen, BLUE, (50, self.p1_y, self.paddle_w, self.paddle_h))
        pygame.draw.rect(self.screen, RED, (SCREEN_WIDTH - 50 - self.paddle_w, self.p2_y, self.paddle_w, self.paddle_h))
        
        # Ball
        pygame.draw.circle(self.screen, YELLOW, (int(self.ball_x), int(self.ball_y)), 10)
        
        # Scores
        s1 = self.font.render(str(self.score_p1), True, WHITE)
        s2 = self.font.render(str(self.score_p2), True, WHITE)
        self.screen.blit(s1, (SCREEN_WIDTH//4, 50))
        self.screen.blit(s2, (3*SCREEN_WIDTH//4, 50))
        
        if self.winner:
            win_text = self.font.render(self.winner, True, WHITE)
            self.screen.blit(win_text, (SCREEN_WIDTH//2 - win_text.get_width()//2, SCREEN_HEIGHT//2))

class DodgeballMinigame:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.reset()
        
    def reset(self):
        self.player_rect = pygame.Rect(SCREEN_WIDTH//2, SCREEN_HEIGHT - 60, 40, 40)
        self.speed = 5
        self.falling_objects = []
        self.spawn_timer = 0
        self.score = 0
        self.health = 3
        self.winner = None
        self.game_over_timer = 0
        
    def handle_input(self, keys, joystick=None):
        if self.winner: return
        
        dx = 0
        if keys[pygame.K_LEFT]: dx = -1
        if keys[pygame.K_RIGHT]: dx = 1
        
        if joystick:
            axis = joystick.get_axis(0)
            if abs(axis) > 0.1: dx = axis
            
        self.player_rect.x += dx * self.speed
        self.player_rect.clamp_ip(self.screen.get_rect())
        
    def update(self):
        if self.winner:
            self.game_over_timer += 1
            return self.winner if self.game_over_timer > 180 else None
            
        self.spawn_timer += 1
        if self.spawn_timer > 30: # Spawn every 30 frames
            x = random.randint(0, SCREEN_WIDTH - 20)
            self.falling_objects.append(pygame.Rect(x, -20, 20, 20))
            self.spawn_timer = 0
            
        for obj in self.falling_objects[:]:
            obj.y += 5
            if obj.colliderect(self.player_rect):
                self.health -= 1
                self.falling_objects.remove(obj)
            elif obj.y > SCREEN_HEIGHT:
                self.falling_objects.remove(obj)
                self.score += 1
                
        if self.health <= 0:
            self.winner = "Game Over! Score: " + str(self.score)
        
        if self.score >= 20: # Win condition
             self.winner = "You Survived! Win!"
            
        return None

    def draw(self):
        self.screen.fill((20, 0, 20))
        
        # Player
        pygame.draw.rect(self.screen, BLUE, self.player_rect)
        
        # Objects
        for obj in self.falling_objects:
            pygame.draw.circle(self.screen, RED, obj.center, 10)
            
        # HUD
        score_text = self.font.render(f"Score: {self.score}/20", True, WHITE)
        health_text = self.font.render(f"HP: {self.health}", True, RED)
        self.screen.blit(score_text, (20, 20))
        self.screen.blit(health_text, (SCREEN_WIDTH - 150, 20))
        
        if self.winner:
            win_text = self.font.render(self.winner, True, WHITE)
            self.screen.blit(win_text, (SCREEN_WIDTH//2 - win_text.get_width()//2, SCREEN_HEIGHT//2))

class TargetMinigame:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.reset()
        
    def reset(self):
        self.crosshair_rect = pygame.Rect(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 20, 20)
        self.targets = []
        self.score = 0
        self.timer = 600 # 10 seconds
        self.spawn_timer = 0
        self.winner = None
        self.game_over_timer = 0
        
    def handle_input(self, keys, joystick=None):
        if self.winner: return
        
        dx, dy = 0, 0
        speed = 7
        
        if keys[pygame.K_LEFT]: dx = -1
        if keys[pygame.K_RIGHT]: dx = 1
        if keys[pygame.K_UP]: dy = -1
        if keys[pygame.K_DOWN]: dy = 1
        
        if joystick:
            ax = joystick.get_axis(0)
            ay = joystick.get_axis(1)
            if abs(ax) > 0.1: dx = ax
            if abs(ay) > 0.1: dy = ay
            
        self.crosshair_rect.x += dx * speed
        self.crosshair_rect.y += dy * speed
        self.crosshair_rect.clamp_ip(self.screen.get_rect())
        
        # Shoot
        shoot = False
        if keys[pygame.K_SPACE]: shoot = True # Needs debouncing really, but we'll just check hit
        if joystick and joystick.get_button(0): shoot = True
        
        # Simple "just pressed" check logic handled by removing target on hit
        if shoot:
            for t in self.targets[:]:
                if self.crosshair_rect.colliderect(t):
                    self.targets.remove(t)
                    self.score += 1
                    
    def update(self):
        if self.winner:
            self.game_over_timer += 1
            return self.winner if self.game_over_timer > 180 else None
            
        self.timer -= 1
        if self.timer <= 0:
            self.winner = f"Time's Up! Score: {self.score}"
            
        self.spawn_timer += 1
        if self.spawn_timer > 40:
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(50, SCREEN_HEIGHT - 50)
            self.targets.append(pygame.Rect(x, y, 40, 40))
            self.spawn_timer = 0
            
        return None

    def draw(self):
        self.screen.fill(WHITE)
        
        for t in self.targets:
            pygame.draw.circle(self.screen, RED, t.center, 20)
            pygame.draw.circle(self.screen, WHITE, t.center, 15)
            pygame.draw.circle(self.screen, RED, t.center, 10)
            
        # Crosshair
        pygame.draw.line(self.screen, BLACK, (self.crosshair_rect.centerx - 10, self.crosshair_rect.centery), (self.crosshair_rect.centerx + 10, self.crosshair_rect.centery), 2)
        pygame.draw.line(self.screen, BLACK, (self.crosshair_rect.centerx, self.crosshair_rect.centery - 10), (self.crosshair_rect.centerx, self.crosshair_rect.centery + 10), 2)
        
        # HUD
        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        time_text = self.font.render(f"Time: {self.timer // 60}", True, BLACK)
        self.screen.blit(score_text, (20, 20))
        self.screen.blit(time_text, (SCREEN_WIDTH - 200, 20))
        
        if self.winner:
            win_text = self.font.render(self.winner, True, BLACK)
            self.screen.blit(win_text, (SCREEN_WIDTH//2 - win_text.get_width()//2, SCREEN_HEIGHT//2))

class CoinMinigame:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.reset()
        
    def reset(self):
        self.player_rect = pygame.Rect(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 40, 40)
        self.coins = []
        self.score = 0
        self.timer = 600 # 10 seconds
        self.winner = None
        self.game_over_timer = 0
        
        # Spawn initial coins
        for _ in range(10):
            self.spawn_coin()
            
    def spawn_coin(self):
        x = random.randint(50, SCREEN_WIDTH - 50)
        y = random.randint(50, SCREEN_HEIGHT - 50)
        self.coins.append(pygame.Rect(x, y, 20, 20))
        
    def handle_input(self, keys, joystick=None):
        if self.winner: return
        
        dx, dy = 0, 0
        speed = 6
        
        if keys[pygame.K_LEFT]: dx = -1
        if keys[pygame.K_RIGHT]: dx = 1
        if keys[pygame.K_UP]: dy = -1
        if keys[pygame.K_DOWN]: dy = 1
        
        if joystick:
            ax = joystick.get_axis(0)
            ay = joystick.get_axis(1)
            if abs(ax) > 0.1: dx = ax
            if abs(ay) > 0.1: dy = ay
            
        self.player_rect.x += dx * speed
        self.player_rect.y += dy * speed
        self.player_rect.clamp_ip(self.screen.get_rect())
        
        # Collect
        for c in self.coins[:]:
            if self.player_rect.colliderect(c):
                self.coins.remove(c)
                self.score += 1
                self.spawn_coin() # Keep spawning
                
    def update(self):
        if self.winner:
            self.game_over_timer += 1
            return self.winner if self.game_over_timer > 180 else None
            
        self.timer -= 1
        if self.timer <= 0:
            self.winner = f"Time's Up! Coins: {self.score}"
            
        return None

    def draw(self):
        self.screen.fill((0, 100, 100))
        
        # Player
        pygame.draw.rect(self.screen, ORANGE, self.player_rect)
        
        # Coins
        for c in self.coins:
            pygame.draw.circle(self.screen, YELLOW, c.center, 10)
            
        # HUD
        score_text = self.font.render(f"Coins: {self.score}", True, WHITE)
        time_text = self.font.render(f"Time: {self.timer // 60}", True, WHITE)
        self.screen.blit(score_text, (20, 20))
        self.screen.blit(time_text, (SCREEN_WIDTH - 200, 20))
        
        if self.winner:
            win_text = self.font.render(self.winner, True, WHITE)
            self.screen.blit(win_text, (SCREEN_WIDTH//2 - win_text.get_width()//2, SCREEN_HEIGHT//2))

import pygame
import sys
import random
import json
import os
from pygame import mixer

# Инициализация Pygame и mixer
pygame.init()
mixer.init()

# Константы
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
PADDLE_SPEED = 8
BALL_SPEED = 7

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
NEON_BLUE = (0, 255, 255)
NEON_PINK = (255, 20, 147)
NEON_GREEN = (57, 255, 20)
NEON_RED = (255, 0, 102)

# Состояния игры
MENU = 'menu'
SCORE_SELECT = 'score_select'
GAME = 'game'
GAME_OVER = 'game_over'
PAUSE = 'pause'
LEADERBOARD = 'leaderboard'
SETTINGS = 'settings'

# Настройки
class Settings:
    def __init__(self):
        self.sound_enabled = True
        self.load_settings()
        
    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                data = json.load(f)
                self.sound_enabled = data.get('sound_enabled', True)
        except:
            self.sound_enabled = True
            
    def save_settings(self):
        with open('settings.json', 'w') as f:
            json.dump({'sound_enabled': self.sound_enabled}, f)

SETTINGS_MANAGER = Settings()

# Создаем класс для dummy-звука
class DummySound:
    def play(self, *args, **kwargs):
        pass

class GameSound:
    def __init__(self, sound):
        self.sound = sound
        
    def play(self, *args, **kwargs):
        if SETTINGS_MANAGER.sound_enabled:
            self.sound.play(*args, **kwargs)

# Загрузка звуков
try:
    PADDLE_HIT = GameSound(mixer.Sound('paddle_hit.wav'))
    SCORE_SOUND = GameSound(mixer.Sound('score.wav'))
    BUTTON_CLICK = GameSound(mixer.Sound('button_click.wav'))
    WINNER_SOUND = GameSound(mixer.Sound('winner.wav'))
except:
    print("Звуковые файлы не найдены. Игра продолжится без звука.")
    PADDLE_HIT = SCORE_SOUND = BUTTON_CLICK = WINNER_SOUND = DummySound()

# Загрузка рекордов
def load_leaderboard():
    try:
        with open('leaderboard.json', 'r') as f:
            return json.load(f)
    except:
        return []

def save_leaderboard(leaderboard):
    with open('leaderboard.json', 'w') as f:
        json.dump(leaderboard, f)

class Button:
    def __init__(self, x, y, width, height, text, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.font = pygame.font.Font(None, 36)
        
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, 2)
        # Свечение
        for i in range(3):
            pygame.draw.rect(screen, self.color, 
                           pygame.Rect(self.rect.x - i, self.rect.y - i, 
                                     self.rect.width + i*2, self.rect.height + i*2), 1)
        text_surface = self.font.render(self.text, True, self.color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class ExitButton:
    def __init__(self):
        self.size = 30
        self.x = WINDOW_WIDTH - self.size - 10
        self.y = 10
        self.color = NEON_RED
        
    def draw(self, screen):
        # Рисуем крестик
        pygame.draw.line(screen, self.color, 
                        (self.x, self.y), 
                        (self.x + self.size, self.y + self.size), 3)
        pygame.draw.line(screen, self.color, 
                        (self.x, self.y + self.size), 
                        (self.x + self.size, self.y), 3)
        # Свечение
        for i in range(3):
            pygame.draw.line(screen, self.color, 
                           (self.x - i, self.y - i), 
                           (self.x + self.size + i, self.y + self.size + i), 1)
            pygame.draw.line(screen, self.color, 
                           (self.x - i, self.y + self.size + i), 
                           (self.x + self.size + i, self.y - i), 1)
            
    def is_clicked(self, pos):
        return (self.x <= pos[0] <= self.x + self.size and 
                self.y <= pos[1] <= self.y + self.size)

class Paddle:
    def __init__(self, x: int, y: int, is_left: bool):
        self.width = 15
        self.height = 90
        self.x = x
        self.y = y
        self.speed = PADDLE_SPEED
        self.color = NEON_BLUE if is_left else NEON_PINK
        self.score = 0
        self.is_left = is_left

    def move(self, up: bool):
        if up and self.y > 0:
            self.y -= self.speed
        elif not up and self.y < WINDOW_HEIGHT - self.height:
            self.y += self.speed

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        # Добавляем свечение
        for i in range(3):
            pygame.draw.rect(screen, self.color, 
                           (self.x - i, self.y - i, 
                            self.width + i*2, self.height + i*2), 1)

class Ball:
    def __init__(self):
        self.size = 15
        self.reset()
        self.color = NEON_GREEN
        self.trail = []
        
    def reset(self):
        self.x = WINDOW_WIDTH // 2
        self.y = WINDOW_HEIGHT // 2
        self.speed_x = BALL_SPEED * random.choice([-1, 1])
        self.speed_y = BALL_SPEED * random.choice([-0.5, 0.5])

    def move(self):
        # Добавляем текущую позицию в след
        self.trail.append((self.x, self.y))
        if len(self.trail) > 5:  # Длина следа
            self.trail.pop(0)
            
        self.x += self.speed_x
        self.y += self.speed_y

        # Отскок от верхней и нижней границы
        if self.y <= 0 or self.y >= WINDOW_HEIGHT - self.size:
            self.speed_y *= -1

    def draw(self, screen):
        # Рисуем след
        for i, pos in enumerate(self.trail):
            alpha = (i + 1) * 50  # Увеличиваем прозрачность
            s = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (15, 15), self.size - i)
            screen.blit(s, (pos[0]-15, pos[1]-15))
            
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)
        # Добавляем свечение
        for i in range(3):
            pygame.draw.circle(screen, self.color, 
                             (int(self.x), int(self.y)), self.size + i*2, 1)

class PauseMenu:
    def __init__(self):
        self.resume_button = Button(WINDOW_WIDTH//2 - 100, 200, 200, 50, "RESUME", NEON_GREEN)
        self.menu_button = Button(WINDOW_WIDTH//2 - 100, 300, 200, 50, "MAIN MENU", NEON_RED)
        
    def draw(self, screen):
        # Полупрозрачный фон
        s = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        s.set_alpha(128)
        s.fill(BLACK)
        screen.blit(s, (0,0))
        
        # Кнопки
        self.resume_button.draw(screen)
        self.menu_button.draw(screen)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Neon Pong")
        self.clock = pygame.time.Clock()
        self.state = MENU
        self.target_score = None
        self.pause_menu = PauseMenu()
        self.leaderboard = load_leaderboard()
        self.init_menu()
        self.init_game()
        
    def init_menu(self):
        # Добавляем кнопки настроек и очистки рекордов
        self.start_button = Button(WINDOW_WIDTH//2 - 100, 100, 200, 50, "START", NEON_GREEN)
        self.leaderboard_button = Button(WINDOW_WIDTH//2 - 100, 175, 200, 50, "LEADERBOARD", NEON_BLUE)
        self.settings_button = Button(WINDOW_WIDTH//2 - 100, 250, 200, 50, "SETTINGS", NEON_BLUE)
        self.exit_button = Button(WINDOW_WIDTH//2 - 100, 325, 200, 50, "EXIT", NEON_RED)
        
        self.score_buttons = [
            Button(WINDOW_WIDTH//2 - 100, 100 + i*60, 200, 50, str(score), NEON_BLUE)
            for i, score in enumerate([20, 30, 40, 50, 60, "Infinity"])
        ]
        
        # Кнопки настроек
        self.sound_button = Button(WINDOW_WIDTH//2 - 100, 150, 200, 50, 
                                 "SOUND: ON" if SETTINGS_MANAGER.sound_enabled else "SOUND: OFF", 
                                 NEON_GREEN)
        self.back_settings_button = Button(WINDOW_WIDTH//2 - 100, 250, 200, 50, 
                                         "BACK", NEON_BLUE)
        
        # Кнопки лидерборда
        self.clear_button = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT - 170, 200, 50, 
                                 "CLEAR", NEON_RED)
        self.back_leaderboard_button = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT - 100, 200, 50, 
                                            "BACK", NEON_GREEN)
        
        self.exit_icon = ExitButton()

    def init_game(self):
        self.paddle_left = Paddle(30, WINDOW_HEIGHT//2 - 45, True)
        self.paddle_right = Paddle(WINDOW_WIDTH - 45, WINDOW_HEIGHT//2 - 45, False)
        self.ball = Ball()
        self.font = pygame.font.Font(None, 74)
        
    def handle_menu_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.state == MENU:
                if self.start_button.is_clicked(event.pos):
                    BUTTON_CLICK.play()
                    self.state = SCORE_SELECT
                elif self.leaderboard_button.is_clicked(event.pos):
                    BUTTON_CLICK.play()
                    self.state = LEADERBOARD
                elif self.settings_button.is_clicked(event.pos):
                    BUTTON_CLICK.play()
                    self.state = SETTINGS
                elif self.exit_button.is_clicked(event.pos):
                    pygame.quit()
                    sys.exit()
            elif self.state == SETTINGS:
                if self.sound_button.is_clicked(event.pos):
                    SETTINGS_MANAGER.sound_enabled = not SETTINGS_MANAGER.sound_enabled
                    SETTINGS_MANAGER.save_settings()
                    self.sound_button.text = "SOUND: ON" if SETTINGS_MANAGER.sound_enabled else "SOUND: OFF"
                    BUTTON_CLICK.play()
                elif self.back_settings_button.is_clicked(event.pos):
                    BUTTON_CLICK.play()
                    self.state = MENU
            elif self.state == SCORE_SELECT:
                for i, button in enumerate(self.score_buttons):
                    if button.is_clicked(event.pos):
                        BUTTON_CLICK.play()
                        self.target_score = float('inf') if i == 5 else [20, 30, 40, 50, 60][i]
                        self.state = GAME
                        self.init_game()
            elif self.state == GAME:
                if self.exit_icon.is_clicked(event.pos):
                    BUTTON_CLICK.play()
                    self.state = MENU
                    self.paddle_left.score = 0
                    self.paddle_right.score = 0
            elif self.state == PAUSE:
                if self.pause_menu.resume_button.is_clicked(event.pos):
                    BUTTON_CLICK.play()
                    self.state = GAME
                elif self.pause_menu.menu_button.is_clicked(event.pos):
                    BUTTON_CLICK.play()
                    self.state = MENU
            elif self.state == LEADERBOARD:
                if self.clear_button.is_clicked(event.pos):
                    BUTTON_CLICK.play()
                    self.leaderboard = []
                    save_leaderboard([])
                elif self.back_leaderboard_button.is_clicked(event.pos):
                    BUTTON_CLICK.play()
                    self.state = MENU

    def draw_menu(self):
        self.screen.fill(BLACK)
        if self.state == MENU:
            self.start_button.draw(self.screen)
            self.leaderboard_button.draw(self.screen)
            self.settings_button.draw(self.screen)
            self.exit_button.draw(self.screen)
        elif self.state == SETTINGS:
            title = self.font.render("SETTINGS", True, NEON_GREEN)
            title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 50))
            self.screen.blit(title, title_rect)
            self.sound_button.draw(self.screen)
            self.back_settings_button.draw(self.screen)
        elif self.state == SCORE_SELECT:
            title = self.font.render("Select Score Limit", True, NEON_GREEN)
            title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 50))
            self.screen.blit(title, title_rect)
            for button in self.score_buttons:
                button.draw(self.screen)
        pygame.display.flip()

    def draw_leaderboard(self):
        self.screen.fill(BLACK)
        title = self.font.render("LEADERBOARD", True, NEON_GREEN)
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 50))
        self.screen.blit(title, title_rect)
        
        # Отображаем топ-10 результатов
        small_font = pygame.font.Font(None, 36)
        for i, score in enumerate(sorted(self.leaderboard, reverse=True)[:10]):
            text = small_font.render(f"{i+1}. Score: {score}", True, NEON_BLUE)
            self.screen.blit(text, (WINDOW_WIDTH//2 - 100, 150 + i*40))
            
        # Кнопки
        self.clear_button.draw(self.screen)
        self.back_leaderboard_button.draw(self.screen)
        pygame.display.flip()

    def draw(self):
        if self.state == PAUSE:
            self.pause_menu.draw(self.screen)
        elif self.state == LEADERBOARD:
            self.draw_leaderboard()
        else:
            self.screen.fill(BLACK)
            
            # Рисуем центральную линию
            for i in range(0, WINDOW_HEIGHT, 30):
                pygame.draw.rect(self.screen, WHITE, (WINDOW_WIDTH//2 - 5, i, 10, 15))
            
            # Рисуем счет
            score_left = self.font.render(str(self.paddle_left.score), True, NEON_BLUE)
            score_right = self.font.render(str(self.paddle_right.score), True, NEON_PINK)
            self.screen.blit(score_left, (WINDOW_WIDTH//4, 20))
            self.screen.blit(score_right, (3*WINDOW_WIDTH//4, 20))
            
            # Рисуем ракетки и мяч
            self.paddle_left.draw(self.screen)
            self.paddle_right.draw(self.screen)
            self.ball.draw(self.screen)
            
            pygame.display.flip()

    def update(self):
        if self.state == GAME:
            self.ball.move()
            self.check_collisions()

    def check_win_condition(self):
        if self.target_score != float('inf'):
            if (self.paddle_left.score >= self.target_score or 
                self.paddle_right.score >= self.target_score):
                self.draw_game_over()

    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_ESCAPE] and self.state == GAME:
            self.state = PAUSE
        elif keys[pygame.K_ESCAPE] and self.state == PAUSE:
            self.state = GAME
            
        if self.state == GAME:
            if keys[pygame.K_w]:
                self.paddle_left.move(True)
            if keys[pygame.K_s]:
                self.paddle_left.move(False)
            if keys[pygame.K_UP]:
                self.paddle_right.move(True)
            if keys[pygame.K_DOWN]:
                self.paddle_right.move(False)

    def check_collisions(self):
        # Проверка столкновения с ракетками
        if self.ball.x <= self.paddle_left.x + self.paddle_left.width and \
           self.paddle_left.y <= self.ball.y <= self.paddle_left.y + self.paddle_left.height:
            PADDLE_HIT.play()
            self.ball.x = self.paddle_left.x + self.paddle_left.width
            self.ball.speed_x *= -1.1
            
        elif self.ball.x >= self.paddle_right.x - self.ball.size and \
             self.paddle_right.y <= self.ball.y <= self.paddle_right.y + self.paddle_right.height:
            PADDLE_HIT.play()
            self.ball.x = self.paddle_right.x - self.ball.size
            self.ball.speed_x *= -1.1

        # Проверка на гол
        if self.ball.x < 0:
            SCORE_SOUND.play()
            self.paddle_right.score += 1
            self.ball.reset()
        elif self.ball.x > WINDOW_WIDTH:
            SCORE_SOUND.play()
            self.paddle_left.score += 1
            self.ball.reset()

    def draw_game_over(self):
        self.screen.fill(BLACK)
        winner = "LEFT" if self.paddle_left.score > self.paddle_right.score else "RIGHT"
        winner_color = NEON_BLUE if winner == "LEFT" else NEON_PINK
        
        WINNER_SOUND.play()
        
        # Добавляем счет в таблицу рекордов
        max_score = max(self.paddle_left.score, self.paddle_right.score)
        self.leaderboard.append(max_score)
        save_leaderboard(self.leaderboard)
        
        # Отображаем победителя
        text = self.font.render(f"{winner} WINS!", True, winner_color)
        text_rect = text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 50))
        self.screen.blit(text, text_rect)
        
        score_text = self.font.render(f"{self.paddle_left.score} - {self.paddle_right.score}", 
                                    True, WHITE)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 50))
        self.screen.blit(score_text, score_rect)
        
        back_button = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 + 100, 200, 50, 
                           "Back to Menu", NEON_GREEN)
        back_button.draw(self.screen)
        
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if back_button.is_clicked(event.pos):
                        BUTTON_CLICK.play()
                        waiting = False
                        self.state = MENU
                        self.paddle_left.score = 0
                        self.paddle_right.score = 0

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.handle_menu_input(event)

            self.handle_input()
            
            if self.state in [MENU, SCORE_SELECT, SETTINGS]:
                self.draw_menu()
            elif self.state == GAME or self.state == PAUSE:
                if self.state == GAME:
                    self.update()
                self.draw()
                self.exit_icon.draw(self.screen)
                pygame.display.flip()
                self.check_win_condition()
            elif self.state == LEADERBOARD:
                self.draw_leaderboard()

            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()

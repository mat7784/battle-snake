import pygame
import sys
import time

# Constants for colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Constants for game settings
WIDTH, HEIGHT = 1000, 800
PLAYER_WIDTH, PLAYER_HEIGHT = 30, 30
PLAYER_VELOCITY = 3
TRAIL_LENGTH = 3
TRAIL_WIDTH = 5
SAFE_ZONE = 13
BG_IMAGE_PATH = "bg1.png"
FONT_NAME = "comicsans"
FONT_SIZE = 30

# Key bindings for two players
PLAYER1_KEYS = {pygame.K_LEFT: "LEFT", pygame.K_RIGHT: "RIGHT", pygame.K_UP: "UP", pygame.K_DOWN: "DOWN"}
PLAYER2_KEYS = {pygame.K_a: "LEFT", pygame.K_d: "RIGHT", pygame.K_w: "UP", pygame.K_s: "DOWN"}

# Constants for menu
MENU_OPTIONS = ["Start Game", "Instructions", "Settings", "Quit"]
MENU_FONT_SIZE = 40
BUTTON_COLORS = [WHITE, WHITE, WHITE]  # Default button colors
HOVER_COLORS = [(200, 200, 200), (200, 200, 200), (200, 200, 200)]  # Colors when hovering


class Player:
    def __init__(self, x, y, width, height, color, key_bindings):
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.color = color
        self.key_bindings = key_bindings
        self.reset()

    def reset(self):
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.direction = "UP"
        self.trail = []
        self.death_count = 0

    def move(self):
        keys = pygame.key.get_pressed()
        for key, direction in self.key_bindings.items():
            if keys[key] and self.direction != self.opposite_direction(direction):
                self.direction = direction

        if self.direction == "UP" and self.rect.top > 0:
            self.rect.y -= PLAYER_VELOCITY
        elif self.direction == "DOWN" and self.rect.bottom < HEIGHT:
            self.rect.y += PLAYER_VELOCITY
        elif self.direction == "RIGHT" and self.rect.right < WIDTH:
            self.rect.x += PLAYER_VELOCITY
        elif self.direction == "LEFT" and self.rect.left > 0:
            self.rect.x -= PLAYER_VELOCITY

    def update_trail(self, game_state):
        if game_state != "PAUSED":
            current_time = time.time()
            self.trail.append((self.rect.center, current_time))
            self.trail = [(pos, t) for pos, t in self.trail if current_time - t <= TRAIL_LENGTH]

    def draw_trail(self, window):
        safe_zone_color = (0, 255, 0)  # Green color for safe zone segments
        for i in range(len(self.trail) - 1):
            if i >= len(self.trail) - SAFE_ZONE:
                color = safe_zone_color  # Use different color for safe zone
            else:
                color = self.color  # Normal color for other segments
            pygame.draw.line(window, color, self.trail[i][0], self.trail[i + 1][0], TRAIL_WIDTH)

    def check_collision(self, other_trail):
        # Check collision with own trail
        for segment in self.trail[:-SAFE_ZONE]:
            if self.rect.colliderect(self.segment_to_rect(segment)):
                return True
        # Check collision with other player's trail
        for segment in other_trail[:-SAFE_ZONE]:
            if self.rect.colliderect(self.segment_to_rect(segment)):
                return True
        return False

    def segment_to_rect(self, segment):
        segment_pos = segment[0]
        return pygame.Rect(segment_pos[0] - TRAIL_WIDTH // 2, segment_pos[1] - TRAIL_WIDTH // 2, TRAIL_WIDTH,
                           TRAIL_WIDTH)

    def check_collision_with_segment(self, segment):
        segment_rect = pygame.Rect(segment[0][0] - TRAIL_WIDTH // 2, segment[0][1] - TRAIL_WIDTH // 2, TRAIL_WIDTH, TRAIL_WIDTH)
        return self.rect.colliderect(segment_rect)

    def adjust_trail_time(self, duration):
        self.trail = [(pos, t + duration) for pos, t in self.trail]

    @staticmethod
    def opposite_direction(direction):
        return {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}[direction]


class Game:
    def __init__(self):
        pygame.init()
        self.fullscreen = False
        self.screen_info = pygame.display.Info()  # Get current display info
        self.fullscreen_size = (self.screen_info.current_w, self.screen_info.current_h)  # Fullscreen resolution
        self.original_resolution = (WIDTH, HEIGHT)  # Original game resolution
        self.window_surface = pygame.Surface(self.original_resolution)
        self.set_display_mode()
        pygame.display.set_caption("Trail Game")
        self.background = pygame.transform.scale(pygame.image.load(BG_IMAGE_PATH), (WIDTH, HEIGHT))
        self.font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)
        self.menu_font = pygame.font.SysFont(FONT_NAME, MENU_FONT_SIZE)
        self.clock = pygame.time.Clock()
        self.player1 = Player(800, HEIGHT - PLAYER_HEIGHT - 100, PLAYER_WIDTH, PLAYER_HEIGHT, RED, PLAYER1_KEYS)
        self.player2 = Player(100, HEIGHT - PLAYER_HEIGHT - 100, PLAYER_WIDTH, PLAYER_HEIGHT, BLUE, PLAYER2_KEYS)
        self.state = "MENU"
        self.pause_start_time = 0
        self.settings_state = "MAIN"
        self.settings_options = ["Toggle Fullscreen", "Change Key Bindings"]
        self.settings_rects = []

    def set_display_mode(self):
        if self.fullscreen:
            self.window = pygame.display.set_mode(self.fullscreen_size, pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode(self.original_resolution)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.set_display_mode()

    def handle_gameplay(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # Pause the game
                    self.state = "PAUSED"
                elif event.key == pygame.K_F11:  # Toggle fullscreen
                    self.toggle_fullscreen()

        # Update player positions and trails
        self.player1.move()
        self.player1.update_trail(self.state)
        self.player2.move()
        self.player2.update_trail(self.state)

        # Check for collisions
        if self.player1.check_collision(self.player2.trail) or self.player2.check_collision(self.player1.trail):
            self.player1.death_count += 1
            self.player2.death_count += 1
            self.player1.reset()
            self.player2.reset()

        # Draw game elements
        self.draw_game()

    def handle_pause(self):
        pause_start_time = time.time()
        while self.state == "PAUSED":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pause_duration = time.time() - pause_start_time
                        self.player1.adjust_trail_time(pause_duration)
                        self.player2.adjust_trail_time(pause_duration)
                        self.state = "GAME"
                    elif event.key == pygame.K_BACKSPACE:
                        self.state = "MENU"

            self.window.blit(self.background, (0, 0))
            self.draw_game()
            self.draw_text("Paused - ESC to Resume, Backspace for Menu", WIDTH // 2 - 200, HEIGHT // 2)
            pygame.display.update()

    def run(self):
        while True:
            if self.state == "MENU":
                self.handle_menu()
            elif self.state == "GAME":
                self.handle_gameplay()
            elif self.state == "SETTINGS":
                self.handle_settings()
            elif self.state == "PAUSED":
                self.handle_pause()
            elif self.state == "INSTRUCTIONS":
                self.handle_instructions()
            else:
                break
            self.clock.tick(60)

    def handle_menu(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for index, option_rect in enumerate(self.get_menu_option_rects()):
                    if option_rect.collidepoint(mouse_x, mouse_y):
                        self.handle_menu_option_selection(index)
                        break
                    elif index == 2:  # Handling selection of the Settings option
                        self.state = "SETTINGS"

        self.window.blit(self.background, (0, 0))
        self.draw_menu(mouse_x, mouse_y)
        pygame.display.update()

    def handle_settings(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.settings_rects = self.get_settings_option_rects()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for index, rect in enumerate(self.settings_rects):
                    if rect.collidepoint(mouse_x, mouse_y):
                        if index == 0:
                            self.toggle_fullscreen()
                        elif index == 1:
                            self.change_key_bindings()
                        break

        self.window.blit(self.background, (0, 0))
        self.draw_settings_menu(mouse_x, mouse_y)
        self.draw_player_key_bindings()
        pygame.display.update()

    def get_settings_option_rects(self):
        rects = []
        for index, option in enumerate(self.settings_options):
            text_surface = self.font.render(option, True, WHITE)
            text_rect = text_surface.get_rect(center=(WIDTH // 2, 150 + index * 50))
            rects.append(text_rect)
        return rects
    def get_menu_option_rects(self):
        rects = []
        for index, option in enumerate(MENU_OPTIONS):
            text_surface = self.menu_font.render(option, True, WHITE)
            text_rect = text_surface.get_rect(center=(WIDTH // 2, 150 + index * 100))
            rects.append(text_rect)
        return rects
    def handle_instructions(self):
        # Handle instructions screen here
        pass
    def handle_menu_option_selection(self, index):
        if index == 0:
            self.state = "GAME"
        elif index == 1:
            self.state = "INSTRUCTIONS"
        elif index == 2:
            self.state = "SETTINGS"
        elif index == 3:
            pygame.quit()
            sys.exit()

    def draw_menu(self, mouse_x, mouse_y):
        for index, option in enumerate(MENU_OPTIONS):
            text_surface = self.menu_font.render(option, True, WHITE)
            text_rect = text_surface.get_rect(center=(WIDTH // 2, 150 + index * 100))
            if text_rect.collidepoint(mouse_x, mouse_y):
                pygame.draw.rect(self.window, HOVER_COLORS[index], text_rect)
            self.window.blit(text_surface, text_rect)

    def draw_settings_menu(self, mouse_x, mouse_y):
        for index, option in enumerate(self.settings_options):
            text_surface = self.font.render(option, True, WHITE)
            text_rect = text_surface.get_rect(center=(WIDTH // 2, 150 + index * 50))
            if text_rect.collidepoint(mouse_x, mouse_y):
                pygame.draw.rect(self.window, HOVER_COLORS[index], text_rect)
            self.window.blit(text_surface, text_rect)

    def change_key_bindings(self):
        # Placeholder for changing key bindings logic
        print("Change Key Bindings option selected")

    def draw_game(self):
        # Draw to the game's surface
        self.window_surface.blit(self.background, (0, 0))
        self.player1.draw_trail(self.window_surface)
        self.player2.draw_trail(self.window_surface)
        pygame.draw.rect(self.window_surface, self.player1.color, self.player1.rect)
        pygame.draw.rect(self.window_surface, self.player2.color, self.player2.rect)
        self.draw_text_on_surface(f"Player 1 Deaths: {self.player1.death_count}", 10, 35, self.window_surface)
        self.draw_text_on_surface(f"Player 2 Deaths: {self.player2.death_count}", WIDTH - 200, 35, self.window_surface)

        if self.fullscreen:
            # Scale the surface proportionally
            scale = min(self.fullscreen_size[0] / WIDTH, self.fullscreen_size[1] / HEIGHT)
            new_width = int(WIDTH * scale)
            new_height = int(HEIGHT * scale)
            scaled_surface = pygame.transform.scale(self.window_surface, (new_width, new_height))

            # Center the scaled surface
            x = (self.fullscreen_size[0] - new_width) // 2
            y = (self.fullscreen_size[1] - new_height) // 2
            self.window.blit(scaled_surface, (x, y))
        else:
            self.window.blit(self.window_surface, (0, 0))

        pygame.display.update()

    def draw_player_key_bindings(self):
        # Draw key bindings for Player 1
        y_offset = 300  # Starting y position for key bindings
        self.draw_text("Player 1 Key Bindings:", WIDTH // 8, y_offset)
        for key, action in PLAYER1_KEYS.items():
            key_name = pygame.key.name(key)
            self.draw_text(f"{action}: {key_name}", WIDTH // 8, y_offset + 30)
            y_offset += 30

        # Draw key bindings for Player 2
        y_offset = 300  # Reset y position for Player 2
        self.draw_text("Player 2 Key Bindings:", 4 * WIDTH // 8, y_offset)
        for key, action in PLAYER2_KEYS.items():
            key_name = pygame.key.name(key)
            self.draw_text(f"{action}: {key_name}", 4 * WIDTH // 8, y_offset + 30)
            y_offset += 30

    def draw_text_on_surface(self, text, x, y, surface):
        text_surface = self.font.render(text, True, WHITE)
        surface.blit(text_surface, (x, y))
    def draw_text(self, text, x, y, surface=None):
        if surface is None:
            surface = self.window
        text_surface = self.font.render(text, True, WHITE)
        surface.blit(text_surface, (x, y))


if __name__ == "__main__":
    game = Game()
    game.run()

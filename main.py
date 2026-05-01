# ============================================================
#  SHOOT 'EM UP  –  Classic 2D arcade game
#  Written with Pygame.  Install with:  pip install pygame
# ============================================================

import pygame
import random
import sys
import os

# ── Window & frame-rate ─────────────────────────────────────
SCREEN_W  = 1200
SCREEN_H  = 1000
FPS       = 60          # frames per second

# ── Colours (R, G, B) ────────────────────────────────────────
BLACK     = (  0,   0,   0)
WHITE     = (255, 255, 255)
RED       = (220,  30,  30)
GREEN     = ( 30, 220,  30)
CYAN      = (  0, 220, 220)
YELLOW    = (220, 220,   0)
ORANGE    = (220, 140,   0)
GREY      = (100, 100, 100)
DARK_BLUE = (  0,   0,  60)

# ── Level definitions ────────────────────────────────────────
# Each level sets:
#   rows          – how many rows of enemies appear
#   cols          – how many enemies per row
#   enemy_speed   – how fast enemies drift sideways (px/frame)
#   bullet_rate   – enemy fires a bullet every N frames
#                   (2/sec at 60fps = every 30 frames, shared across all enemies)
#   drop_speed    – how far enemies drop when they hit a wall (px)
LEVELS = {
    "easy": {
        "rows": 1,
        "cols": 5,
        "enemy_speed": 1,
        "bullet_rate": 10,   # ~2 bullets/sec (one random enemy fires every 30 frames)
        "drop_speed": 12,
        "enemy_image": "enemy1.png",   # image used for level 1 enemies
    },
    "medium": {
        "rows": 3,
        "cols": 9,
        "enemy_speed": 2,
        "bullet_rate": 20,
        "drop_speed": 16,
        "enemy_image": "enemy2.png",   # image used for level 2 enemies
    },
    "hard": {
        "rows": 3,
        "cols": 10,
        "enemy_speed": 3,
        "bullet_rate": 30,
        "drop_speed": 20,
        "enemy_image": "enemy3.png",   # image used for level 3 enemies
    },
}

# The order levels are played through.
# Choosing "medium" on the menu skips easy and plays medium → hard.
LEVEL_ORDER = ["easy", "medium", "hard"]

# ── Player fire-rate ─────────────────────────────────────────
# Player fires 5 bullets per second → one bullet every 12 frames (60 fps / 5)
PLAYER_FIRE_DELAY = 12   # frames between player shots

# ── Sprite sizes ─────────────────────────────────────────────
PLAYER_W,  PLAYER_H  = 80, 100
ENEMY_W,   ENEMY_H   = 60, 60
BULLET_W,  BULLET_H  = 4,  12


# ════════════════════════════════════════════════════════════
#  DRAWING HELPERS  – draw simple pixel-art jets with pygame
# ════════════════════════════════════════════════════════════

def draw_player_jet(surface, x, y):
    """Draw the player's jet (pointing UP, green/cyan tones)."""
    # Body of the jet
    pygame.draw.rect(surface, GREEN,  (x+18, y+6,  12, 20))
    # Left wing
    pygame.draw.polygon(surface, CYAN, [
        (x+6,  y+26), (x+18, y+10), (x+18, y+26)
    ])
    # Right wing
    pygame.draw.polygon(surface, CYAN, [
        (x+42, y+26), (x+30, y+10), (x+30, y+26)
    ])
    # Nose (points upward)
    pygame.draw.polygon(surface, WHITE, [
        (x+24, y+2), (x+18, y+12), (x+30, y+12)
    ])
    # Engine glow at the back
    pygame.draw.rect(surface, YELLOW, (x+20, y+26, 8, 4))


def draw_enemy_jet(surface, x, y):
    """Draw an enemy jet (pointing DOWN, red/orange tones)."""
    # Body
    pygame.draw.rect(surface, RED,    (x+14, y+4,  12, 18))
    # Left wing
    pygame.draw.polygon(surface, ORANGE, [
        (x+2,  y+6),  (x+14, y+20), (x+14, y+6)
    ])
    # Right wing
    pygame.draw.polygon(surface, ORANGE, [
        (x+38, y+6),  (x+26, y+20), (x+26, y+6)
    ])
    # Nose (points downward toward player)
    pygame.draw.polygon(surface, YELLOW, [
        (x+20, y+26), (x+14, y+16), (x+26, y+16)
    ])


# ════════════════════════════════════════════════════════════
#  CLASSES
# ════════════════════════════════════════════════════════════

class Bullet:
    """A single bullet moving vertically up or down."""

    def __init__(self, x, y, speed, color, image=None):
        self.x     = x
        self.y     = y
        self.speed = speed    # negative = moves up (player); positive = moves down (enemy)
        self.color = color
        self.image = image    # optional Surface; if set, blit it instead of drawing a rectangle

    def update(self):
        """Move bullet by its speed each frame."""
        self.y += self.speed

    def get_rect(self):
        """Return a Rect for collision detection."""
        return pygame.Rect(self.x, self.y, BULLET_W, BULLET_H)

    def draw(self, surface):
        if self.image:
            # Use the custom image (e.g. energy bead.png for player bullets).
            surface.blit(self.image, (self.x, self.y))
        else:
            # Fall back to a plain coloured rectangle (used by enemy bullets).
            pygame.draw.rect(surface, self.color, (self.x, self.y, BULLET_W, BULLET_H))


class Player:
    """The player's jet – moves in 4 directions and fires upward."""

    def __init__(self):
        # Load the player jet image from the "game assets" folder.
        # os.path.dirname(__file__) gives the folder where main.py lives,
        # so the path works no matter where you run Python from.
        assets_dir = os.path.join(os.path.dirname(__file__), "game assets")

        # Still image – shown when the jet is not moving.
        raw_idle   = pygame.image.load(os.path.join(assets_dir, "jet.png")).convert_alpha()
        self.image_idle   = pygame.transform.scale(raw_idle,   (PLAYER_W, PLAYER_H))

        # Moving image – shown while any movement key is held.
        raw_moving = pygame.image.load(os.path.join(assets_dir, "jet moving.png")).convert_alpha()
        self.image_moving = pygame.transform.scale(raw_moving, (PLAYER_W, PLAYER_H))

        # Player bullet image – energy bead.png scaled to bullet size.
        raw_bead          = pygame.image.load(os.path.join(assets_dir, "energy bead.png")).convert_alpha()
        self.bullet_image = pygame.transform.scale(raw_bead, (BULLET_W, BULLET_H))

        # Sound played every time the player fires a bullet.
        self.gun_sound = pygame.mixer.Sound(os.path.join(assets_dir, "gun shot.mp3"))

        # Sound looped while the jet is moving; stopped when no key is held.
        self.engine_sound = pygame.mixer.Sound(os.path.join(assets_dir, "jet accelerates.mp3"))
        self.engine_playing = False   # tracks whether the engine sound is currently looping

        # Start with the idle image.
        self.image    = self.image_idle
        self.is_moving = False   # updated every frame in handle_input

        # Start centred near the bottom of the screen
        self.x          = SCREEN_W // 2 - PLAYER_W // 2
        self.y          = SCREEN_H - PLAYER_H - 20
        self.speed      = 5            # movement speed in pixels per frame
        self.fire_timer = 0            # frames remaining before next shot is allowed
        self.bullets    = []           # list of active player Bullet objects
        self.lives      = 3
        self.score      = 0

    def handle_input(self, keys):
        """Move the jet based on arrow keys or WASD."""
        # Track whether any movement key is being pressed this frame.
        self.is_moving = (
            keys[pygame.K_LEFT]  or keys[pygame.K_a] or
            keys[pygame.K_RIGHT] or keys[pygame.K_d] or
            keys[pygame.K_UP]    or keys[pygame.K_w] or
            keys[pygame.K_DOWN]  or keys[pygame.K_s]
        )

        # Start the engine sound when movement begins; stop it when movement ends.
        if self.is_moving and not self.engine_playing:
            self.engine_sound.play(loops=-1)   # loops=-1 means loop forever
            self.engine_playing = True
        elif not self.is_moving and self.engine_playing:
            self.engine_sound.stop()
            self.engine_playing = False
        # Move left
        if (keys[pygame.K_LEFT]  or keys[pygame.K_a]) and self.x > 0:
            self.x -= self.speed
        # Move right
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.x < SCREEN_W - PLAYER_W:
            self.x += self.speed
        # Move up – restricted to the lower half so the player stays visible
        if (keys[pygame.K_UP]    or keys[pygame.K_w]) and self.y > SCREEN_H // 2:
            self.y -= self.speed
        # Move down
        if (keys[pygame.K_DOWN]  or keys[pygame.K_s]) and self.y < SCREEN_H - PLAYER_H:
            self.y += self.speed

    def try_fire(self, keys):
        """Fire a bullet if SPACE is held and the cooldown timer has expired."""
        self.fire_timer -= 1           # count down every frame
        if keys[pygame.K_SPACE] and self.fire_timer <= 0:
            # Bullet spawns at the nose of the jet (top-centre)
            bx = self.x + PLAYER_W // 2 - BULLET_W // 2
            by = self.y
            self.bullets.append(Bullet(bx, by, speed=-10, color=CYAN, image=self.bullet_image))
            self.gun_sound.play()      # play the gun shot sound
            self.fire_timer = PLAYER_FIRE_DELAY   # reset cooldown

    def update_bullets(self):
        """Move all bullets and discard any that have left the screen."""
        for b in self.bullets:
            b.update()
        # Keep only bullets still on screen
        self.bullets = [b for b in self.bullets if b.y > -BULLET_H]

    def get_rect(self):
        """Slightly inset hitbox so grazing shots don't feel unfair."""
        return pygame.Rect(self.x + 10, self.y + 6, PLAYER_W - 20, PLAYER_H - 8)

    def draw(self, surface):
        # Swap to the moving image while a direction key is held, idle otherwise.
        self.image = self.image_moving if self.is_moving else self.image_idle
        surface.blit(self.image, (self.x, self.y))
        for b in self.bullets:
            b.draw(surface)


class Enemy:
    """A single enemy jet at a fixed grid position."""

    def __init__(self, x, y, image):
        self.x     = x
        self.y     = y
        self.alive = True    # set to False when shot
        self.image = image   # pre-loaded, pre-scaled Surface for this level

    def get_rect(self):
        return pygame.Rect(self.x + 4, self.y + 4, ENEMY_W - 8, ENEMY_H - 6)

    def draw(self, surface):
        if self.alive:
            surface.blit(self.image, (self.x, self.y))


class EnemyFleet:
    """
    Manages the entire grid of enemy jets.
    - They move sideways together.
    - When they hit a wall they drop down and reverse direction.
    - A random alive enemy fires a bullet every 'bullet_rate' frames.
    """

    def __init__(self, cfg):
        self.speed      = cfg["enemy_speed"]   # sideways speed in px/frame
        self.direction  = 1                    # 1 = moving right, -1 = moving left
        self.drop_speed = cfg["drop_speed"]    # pixels to drop on wall hit
        self.bullets    = []                   # list of active enemy Bullet objects
        self.fire_rate  = cfg["bullet_rate"]   # frames between shots
        self.fire_timer = cfg["bullet_rate"]   # start at full delay

        # Load and scale the enemy image once for the whole fleet.
        assets_dir   = os.path.join(os.path.dirname(__file__), "game assets")
        raw_img      = pygame.image.load(os.path.join(assets_dir, cfg["enemy_image"])).convert_alpha()
        enemy_image  = pygame.transform.scale(raw_img, (ENEMY_W, ENEMY_H))

        # Load and scale the enemy bullet image (energy bead2.png).
        raw_bead          = pygame.image.load(os.path.join(assets_dir, "energy bead2.png")).convert_alpha()
        self.bullet_image = pygame.transform.scale(raw_bead, (BULLET_W, BULLET_H))

        # ── Build the grid ───────────────────────────────────
        rows      = cfg["rows"]
        cols      = cfg["cols"]
        x_start   = 60
        y_start   = 60
        x_spacing = (SCREEN_W - x_start * 2) // cols
        y_spacing = 50

        self.enemies = []
        for row in range(rows):
            for col in range(cols):
                ex = x_start + col * x_spacing
                ey = y_start + row * y_spacing
                # Pass the shared image into each Enemy.
                self.enemies.append(Enemy(ex, ey, enemy_image))

    def alive_enemies(self):
        """Return a list of enemies that are still alive."""
        return [e for e in self.enemies if e.alive]

    def all_dead(self):
        """True when every enemy has been destroyed."""
        return len(self.alive_enemies()) == 0

    def update(self):
        """Called once per frame to move enemies and fire bullets."""
        alive = self.alive_enemies()
        if not alive:
            return

        # Find the fleet's left and right edges
        left_edge  = min(e.x           for e in alive)
        right_edge = max(e.x + ENEMY_W for e in alive)

        # Hit right wall → drop down and turn left
        if right_edge >= SCREEN_W - 10 and self.direction == 1:
            self.direction = -1
            self._drop_all()
        # Hit left wall → drop down and turn right
        elif left_edge <= 10 and self.direction == -1:
            self.direction = 1
            self._drop_all()

        # Move every enemy sideways
        for e in alive:
            e.x += self.speed * self.direction

        # ── Enemy shooting ───────────────────────────────────
        self.fire_timer -= 1
        if self.fire_timer <= 0:
            self.fire_timer = self.fire_rate
            # Pick a random alive enemy to fire
            shooter = random.choice(alive)
            bx = shooter.x + ENEMY_W // 2 - BULLET_W // 2
            by = shooter.y + ENEMY_H
            self.bullets.append(Bullet(bx, by, speed=6, color=RED, image=self.bullet_image))

        # Move enemy bullets and remove off-screen ones
        for b in self.bullets:
            b.update()
        self.bullets = [b for b in self.bullets if b.y < SCREEN_H + BULLET_H]

    def _drop_all(self):
        """Move every enemy down by drop_speed pixels when the fleet hits a side wall."""
        for e in self.enemies:
            e.y += self.drop_speed

    def draw(self, surface):
        for e in self.enemies:
            e.draw(surface)
        for b in self.bullets:
            b.draw(surface)


# ════════════════════════════════════════════════════════════
#  BACKGROUND STARFIELD
# ════════════════════════════════════════════════════════════

def make_stars(n=120):
    """Create n random star positions."""
    return [(random.randint(0, SCREEN_W), random.randint(0, SCREEN_H)) for _ in range(n)]


def scroll_stars(stars):
    """Scroll stars downward each frame for a sense of flying forward."""
    return [(x, (y + 1) % SCREEN_H) for x, y in stars]


def draw_stars(surface, stars):
    for sx, sy in stars:
        pygame.draw.circle(surface, GREY, (sx, sy), 1)


# ════════════════════════════════════════════════════════════
#  HUD (Heads-Up Display)
# ════════════════════════════════════════════════════════════

def draw_hud(surface, font, player, level_name):
    """Draw score, lives and level name at the top of the screen."""
    score_txt = font.render(f"Score: {player.score}", True, WHITE)
    lives_txt = font.render(f"Lives: {player.lives}", True, WHITE)
    level_txt = font.render(f"Level: {level_name.upper()}", True, YELLOW)

    surface.blit(score_txt, (10, 8))
    surface.blit(lives_txt, (SCREEN_W - lives_txt.get_width() - 10, 8))
    surface.blit(level_txt, (SCREEN_W // 2 - level_txt.get_width() // 2, 8))


# ════════════════════════════════════════════════════════════
#  COLLISION DETECTION
# ════════════════════════════════════════════════════════════

def check_player_bullets_vs_enemies(player, fleet):
    """Check if any player bullet has hit an enemy. Award 10 points per kill."""
    for bullet in player.bullets:
        br = bullet.get_rect()
        for enemy in fleet.alive_enemies():
            if br.colliderect(enemy.get_rect()):
                enemy.alive = False          # destroy the enemy
                bullet.y    = -9999          # teleport bullet off-screen (removed next frame)
                player.score += 10
                break                        # one bullet, one enemy


def check_enemy_bullets_vs_player(player, fleet):
    """Check if any enemy bullet has hit the player. Lose a life if so."""
    pr = player.get_rect()
    for bullet in fleet.bullets:
        if bullet.get_rect().colliderect(pr):
            bullet.y     = SCREEN_H + 9999  # remove bullet
            player.lives -= 1


def enemies_reached_bottom(fleet):
    """Return True if any enemy has descended into the player's zone."""
    for e in fleet.alive_enemies():
        if e.y + ENEMY_H >= SCREEN_H - PLAYER_H - 30:
            return True
    return False

def draw_menu(surface, big_font, small_font):
    """Difficulty selection screen shown before the game starts."""
    surface.fill(DARK_BLUE)

    title = big_font.render("SHOOT 'EM UP", True, CYAN)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 110))

    subtitle = small_font.render("Choose your difficulty:", True, WHITE)
    surface.blit(subtitle, (SCREEN_W // 2 - subtitle.get_width() // 2, 195))

    options = [
        ("1  –  EASY   (2 rows)",   GREEN,  250),
        ("2  –  MEDIUM (3 rows)",   YELLOW, 310),
        ("3  –  HARD   (3 rows, faster)", RED, 370),
    ]
    for text, colour, y in options:
        txt = small_font.render(text, True, colour)
        surface.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, y))

    controls = [
        "Arrow keys / WASD  –  Move",
        "SPACE              –  Fire (5 shots/sec)",
    ]
    for i, line in enumerate(controls):
        t = small_font.render(line, True, GREY)
        surface.blit(t, (SCREEN_W // 2 - t.get_width() // 2, 450 + i * 30))


def draw_congratulations(surface, big_font, small_font, score):
    """Special screen shown when the player clears the final (hard) level."""
    surface.fill(DARK_BLUE)

    # Big congratulations message
    line1 = big_font.render("CONGRATULATIONS,", True, CYAN)
    line2 = big_font.render("YOU WON!", True, YELLOW)
    surface.blit(line1, (SCREEN_W // 2 - line1.get_width() // 2, 130))
    surface.blit(line2, (SCREEN_W // 2 - line2.get_width() // 2, 200))

    sc_txt = small_font.render(f"Final Score: {score}", True, WHITE)
    surface.blit(sc_txt, (SCREEN_W // 2 - sc_txt.get_width() // 2, 295))

    hint = small_font.render("M – Main Menu     Q – Quit", True, GREY)
    surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, 380))


def draw_game_over(surface, big_font, small_font, score, won):
    """Defeat screen shown when the player runs out of lives."""
    surface.fill(DARK_BLUE)
    txt   = big_font.render("GAME OVER", True, RED)
    surface.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, 170))

    sc_txt = small_font.render(f"Final Score: {score}", True, WHITE)
    surface.blit(sc_txt, (SCREEN_W // 2 - sc_txt.get_width() // 2, 265))

    hint = small_font.render("M – Main Menu     Q – Quit", True, GREY)
    surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, 360))


def draw_level_complete(surface, big_font, small_font, next_level_name, score):
    """Screen shown between levels when the player clears all enemies."""
    surface.fill(DARK_BLUE)

    txt = big_font.render("LEVEL COMPLETE!", True, CYAN)
    surface.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, 140))

    sc = small_font.render(f"Score so far: {score}", True, WHITE)
    surface.blit(sc, (SCREEN_W // 2 - sc.get_width() // 2, 250))

    nxt = small_font.render(f"Next level: {next_level_name.upper()}", True, YELLOW)
    surface.blit(nxt, (SCREEN_W // 2 - nxt.get_width() // 2, 305))

    hint = small_font.render("Press any key to continue", True, GREY)
    surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, 400))


# ════════════════════════════════════════════════════════════
#  GAME LOOP
# ════════════════════════════════════════════════════════════

def run_game(screen, clock, fonts, start_level_name):
    """
    Play through all levels starting from start_level_name.
    Score and lives carry over between levels.
    Returns 'menu' when the session ends.
    """
    big_font, small_font = fonts

    # Work out which levels to play (start from the chosen difficulty onward).
    # e.g. choosing "medium" plays medium then hard.
    start_idx      = LEVEL_ORDER.index(start_level_name)
    levels_to_play = LEVEL_ORDER[start_idx:]

    # Create the player once so score and lives persist across levels.
    player = Player()
    stars  = make_stars()

    for level_num, level_name in enumerate(levels_to_play):
        is_last = (level_num == len(levels_to_play) - 1)  # True on the final level
        cfg     = LEVELS[level_name]
        fleet   = EnemyFleet(cfg)   # fresh enemy grid for each level

        game_over       = False
        won             = False
        advance_to_next = False     # set True when player presses key on "Level Complete" screen

        # ── Inner loop: play one level ────────────────────────
        while True:
            # 1. Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if game_over and event.type == pygame.KEYDOWN:
                    if won and not is_last:
                        # Any key on the "Level Complete" screen advances to the next level
                        advance_to_next = True
                    elif event.key == pygame.K_m:
                        return 'menu'
                    elif event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()

            # Break out of the level loop when the player is ready for the next level
            if advance_to_next:
                break

            # 2. Update game state (only while the level is still active)
            if not game_over:
                keys = pygame.key.get_pressed()

                player.handle_input(keys)     # move the jet
                player.try_fire(keys)         # shoot if SPACE held
                player.update_bullets()       # advance player bullets

                fleet.update()               # advance enemies + their bullets

                # Check all collisions
                check_player_bullets_vs_enemies(player, fleet)
                check_enemy_bullets_vs_player(player, fleet)

                # Win this level: all enemies destroyed
                if fleet.all_dead():
                    game_over = True
                    won       = True

                # Lose: out of lives or enemies reached the player zone
                if player.lives <= 0 or enemies_reached_bottom(fleet):
                    game_over = True
                    won       = False

            # 3. Draw
            screen.fill(DARK_BLUE)
            stars = scroll_stars(stars)      # scroll stars for motion effect
            draw_stars(screen, stars)

            if game_over and won and not is_last:
                # Between levels: show "Level Complete" and wait for any key
                draw_level_complete(screen, big_font, small_font,
                                    levels_to_play[level_num + 1], player.score)
            elif game_over and won and is_last:
                # Player cleared the final level – show congratulations
                draw_congratulations(screen, big_font, small_font, player.score)
            elif game_over:
                # Player lost – show game over screen
                draw_game_over(screen, big_font, small_font, player.score, won)
            else:
                fleet.draw(screen)
                player.draw(screen)
                draw_hud(screen, small_font, player, level_name)

            pygame.display.flip()            # push the frame to the screen
            clock.tick(FPS)                  # cap at 60 fps

        # If the player lost, stop looping through remaining levels
        if not won:
            break

    return 'menu'


# ════════════════════════════════════════════════════════════
#  MENU LOOP
# ════════════════════════════════════════════════════════════

def run_menu(screen, clock, fonts):
    """Show the main menu until the player picks a difficulty. Returns level name."""
    big_font, small_font = fonts
    key_to_level = {
        pygame.K_1: "easy",
        pygame.K_2: "medium",
        pygame.K_3: "hard",
    }
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key in key_to_level:
                return key_to_level[event.key]   # start the chosen level

        draw_menu(screen, big_font, small_font)
        pygame.display.flip()
        clock.tick(FPS)


# ════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════

def main():
    pygame.init()
    pygame.mixer.init()   # initialise the audio system for playing sounds
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Shoot 'Em Up")
    clock = pygame.time.Clock()

    # Load and loop the background music forever (-1 = infinite loop).
    music_path = os.path.join(os.path.dirname(__file__), "game assets", "no horizon no return.mp3")
    pygame.mixer.music.load(music_path)
    pygame.mixer.music.play(loops=-1)   # starts immediately and loops until the game closes

    big_font   = pygame.font.SysFont("Arial", 52, bold=True)
    small_font = pygame.font.SysFont("Arial", 24)
    fonts      = (big_font, small_font)

    # Outer loop: menu → game → menu → ...
    while True:
        level_name = run_menu(screen, clock, fonts)
        run_game(screen, clock, fonts, level_name)


if __name__ == "__main__":
    main()

import math
import pygame
import asyncio

pygame.init()

WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Crazy Asteroids by Barack Hossain")
clock = pygame.time.Clock()

MISSILE_SPEED = 7
FIRE_DELAY = 100
ROTATION_SPEED = 3
THRUST = 0.15
DRAG = 0.99
MAX_SPEED = 7
DETECTION_RANGE = 300

WHITE = (255, 255, 255)
RED = (255, 55, 55)
GREEN = (0, 255, 0)
font = pygame.font.Font(None, 28)
big_font = pygame.font.Font(None, 72)


class Spaceship:
    def __init__(self, position):
        self.position = pygame.Vector2(position)
        self.angle = 90
        self.radius = 20
        self.velocity = pygame.Vector2(0, 0)
        self.forward = pygame.Vector2(0, -1)

    def update(self, keys):
        if keys[pygame.K_a]:
            self.angle += ROTATION_SPEED
        if keys[pygame.K_d]:
            self.angle -= ROTATION_SPEED

        self.angle %= 360
        radians = math.radians(self.angle)
        self.forward = pygame.Vector2(math.cos(radians), -math.sin(radians))
        if keys[pygame.K_w]:
            self.velocity += self.forward * THRUST
        self.velocity *= DRAG
        if self.velocity.length() > MAX_SPEED:
            self.velocity.scale_to_length(MAX_SPEED)

        self.position += self.velocity
        self.position.x %= WIDTH
        self.position.y %= HEIGHT

    def draw(self):
        points = [
            self.position + self.forward * 22,
            self.position + self.forward.rotate(140) * 16,
            self.position + self.forward.rotate(-140) * 16,
        ]
        pygame.draw.polygon(screen, GREEN, points, 2)


class Missile:
    def __init__(self, position, direction):
        self.position = pygame.Vector2(position)
        self.velocity = direction * MISSILE_SPEED
        self.radius = 6

    def update(self):
        self.position += self.velocity

    def draw(self):
        tail = self.position - self.velocity.normalize() * 16
        pygame.draw.line(screen, WHITE, self.position, tail, 3)


class EnemyBullet:
    def __init__(self, position, direction):
        self.position = pygame.Vector2(position)
        self.velocity = direction * 2
        self.radius = 6

    def update(self):
        self.position += self.velocity

    def draw(self):
        pygame.draw.circle(screen, RED, self.position, self.radius)


class Enemy:
    def __init__(self, position):
        self.position = pygame.Vector2(position)
        self.angle = 0
        self.radius = 25
        self.state = "PATROL"
        self.forward = pygame.Vector2(1, 0)
        self.last_shot = 0
        self.detected_player_at = None
        self.patrol_direction = 1

    def update(self, player, now):
        self.position.x += self.patrol_direction * 0.35
        if self.position.x >= WIDTH - self.radius:
            self.position.x = WIDTH - self.radius
            self.patrol_direction = -1
        elif self.position.x <= self.radius:
            self.position.x = self.radius
            self.patrol_direction = 1

        to_player = player.position - self.position
        distance = to_player.length()
        self.state = "ATTACK" if distance < DETECTION_RANGE else "PATROL"

        if self.state == "ATTACK" and distance > 0:
            if self.detected_player_at is None:
                self.detected_player_at = now
            target_angle = math.degrees(math.atan2(-to_player.y, to_player.x)) % 360
            turn = (target_angle - self.angle + 180) % 360 - 180
            self.angle = (self.angle + max(-2.5, min(2.5, turn))) % 360
        else:
            self.detected_player_at = None

        radians = math.radians(self.angle)
        self.forward = pygame.Vector2(math.cos(radians), -math.sin(radians))

    def shoot(self, player, now):
        if (self.state != "ATTACK" or self.detected_player_at is None or
                now - self.detected_player_at < 3000 or now - self.last_shot < 1600):
            return None
        direction = player.position - self.position
        if direction.length_squared() == 0:
            return None
        self.last_shot = now
        direction = direction.normalize()
        return EnemyBullet(self.position + direction * 30, direction)

    def draw(self):
        color = RED if self.state == "ATTACK" else WHITE
        points = [
            self.position + self.forward * 28,
            self.position + self.forward.rotate(140) * 20,
            self.position + self.forward.rotate(-140) * 20,
        ]
        pygame.draw.polygon(screen, color, points, 2)
        pygame.draw.circle(screen, (55, 55, 55), self.position, DETECTION_RANGE, 1)


def spawn_asteroids():
    positions = [
        pygame.Vector2(120, 120), pygame.Vector2(350, 130),
        pygame.Vector2(600, 170), pygame.Vector2(180, 420),
        pygame.Vector2(450, 390), pygame.Vector2(680, 470),
    ]
    velocities = [
        pygame.Vector2(3.2, 1.8), pygame.Vector2(-2.4, 2.7),
        pygame.Vector2(-3.0, -1.6), pygame.Vector2(2.6, -2.8),
        pygame.Vector2(-2.2, 2.1), pygame.Vector2(-3.1, -2.4),
    ]
    return positions, velocities, [32, 25, 40, 28, 36, 24]


def reset_game():
    global spaceship, enemy, missiles, enemy_bullets
    global positions, velocities, radii, score, lives, game_over, invulnerable_until
    spaceship = Spaceship((400, 300))
    enemy = Enemy((200, 300))
    missiles = []
    enemy_bullets = []
    positions, velocities, radii = spawn_asteroids()
    score = 0
    lives = 3
    game_over = False
    invulnerable_until = 0

async def main():
    global spaceship, enemy, missiles, enemy_bullets
    global positions, velocities, radii, score, lives, game_over, invulnerable_until
    reset_game()
    last_fire_time = 0
    running = True

    while running:
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if game_over and event.key == pygame.K_r:
                    reset_game()
                elif not game_over and event.key == pygame.K_SPACE:
                    if now - last_fire_time >= FIRE_DELAY:
                        missiles.append(Missile(
                            spaceship.position + spaceship.forward * 22,
                            spaceship.forward,
                        ))
                        last_fire_time = now

        if not game_over:
            keys = pygame.key.get_pressed()
            spaceship.update(keys)
            enemy.update(spaceship, now)
            shot = enemy.shoot(spaceship, now)
            if shot:
                enemy_bullets.append(shot)

            for i in range(len(positions)):
                positions[i] += velocities[i]
                if positions[i].x - radii[i] < 0:
                    positions[i].x = radii[i]
                    velocities[i].x = abs(velocities[i].x)
                elif positions[i].x + radii[i] > WIDTH:
                    positions[i].x = WIDTH - radii[i]
                    velocities[i].x = -abs(velocities[i].x)
                if positions[i].y - radii[i] < 0:
                    positions[i].y = radii[i]
                    velocities[i].y = abs(velocities[i].y)
                elif positions[i].y + radii[i] > HEIGHT:
                    positions[i].y = HEIGHT - radii[i]
                    velocities[i].y = -abs(velocities[i].y)

            for i in range(len(positions)):
                for j in range(i + 1, len(positions)):
                    offset = positions[j] - positions[i]
                    distance = offset.length()
                    minimum_distance = radii[i] + radii[j]
                    if distance < minimum_distance:
                        normal = offset.normalize() if distance else pygame.Vector2(1, 0)
                        distance = max(distance, 0.001)
                        overlap = minimum_distance - distance
                        mass_i = radii[i] ** 2
                        mass_j = radii[j] ** 2
                        total_mass = mass_i + mass_j
                        positions[i] -= normal * overlap * (mass_j / total_mass)
                        positions[j] += normal * overlap * (mass_i / total_mass)
                        relative_velocity = velocities[j] - velocities[i]
                        velocity_along_normal = relative_velocity.dot(normal)
                        if velocity_along_normal < 0:
                            impulse = -(2.0 * velocity_along_normal) / ((1 / mass_i) + (1 / mass_j))
                            impulse_vector = impulse * normal
                            velocities[i] -= impulse_vector / mass_i
                            velocities[j] += impulse_vector / mass_j

            for missile in missiles[:]:
                missile.update()
                if (missile.position.x < 0 or missile.position.x > WIDTH or
                        missile.position.y < 0 or missile.position.y > HEIGHT):
                    missiles.remove(missile)
                    continue
                for i in range(len(positions) - 1, -1, -1):
                    if missile.position.distance_to(positions[i]) < missile.radius + radii[i]:
                        positions.pop(i)
                        velocities.pop(i)
                        radii.pop(i)
                        score += 1
                        missiles.remove(missile)
                        break

            if not positions:
                positions, velocities, radii = spawn_asteroids()

            for bullet in enemy_bullets[:]:
                bullet.update()
                if (bullet.position.x < 0 or bullet.position.x > WIDTH or
                        bullet.position.y < 0 or bullet.position.y > HEIGHT):
                    enemy_bullets.remove(bullet)
                elif (now >= invulnerable_until and
                      bullet.position.distance_to(spaceship.position) < bullet.radius + spaceship.radius):
                    enemy_bullets.remove(bullet)
                    lives -= 1
                    invulnerable_until = now + 1200
                    if lives <= 0:
                        game_over = True

        screen.fill((0, 0, 0))
        for position, radius in zip(positions, radii):
            pygame.draw.circle(screen, (150, 150, 150), position, radius)

        enemy.draw()
        if now >= invulnerable_until or (now // 120) % 2 == 0:
            spaceship.draw()
        for missile in missiles:
            missile.draw()
        for bullet in enemy_bullets:
            bullet.draw()

        hud = [
            f"Score: {score}",
            f"Lives: {lives}",
            f"Speed: {spaceship.velocity.length():.1f}",
            f"Enemy: {enemy.state}",
        ]
        for index, text in enumerate(hud):
            screen.blit(font.render(text, True, WHITE), (10, 10 + index * 28))

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            title = big_font.render("GAME OVER", True, RED)
            final_score = font.render(f"Final score: {score}", True, WHITE)
            restart = font.render("Press R to play again", True, WHITE)
            screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 55)))
            screen.blit(final_score, final_score.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 5)))
            screen.blit(restart, restart.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40)))

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())

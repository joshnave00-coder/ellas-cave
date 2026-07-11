"""constants.py — shared constants, pygame init, screen, fonts, helpers."""
import pygame, sys, json, os, math, random

pygame.init()

SCREEN_W, SCREEN_H = 1200, 700
_display = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
pygame.display.set_caption("Ella's Cave")
game_surf = pygame.Surface((SCREEN_W, SCREEN_H))  # internal 1200x700 game surface
screen = game_surf  # all game code draws to game_surf via screen alias
clock = pygame.time.Clock()
FPS = 60

# Physics
GRAVITY    = 0.52
MAX_FALL   = 18
JUMP_VEL   = -17
MOVE_SPEED = 6
ICE_KEY    = pygame.K_x
DOWN_KEY   = pygame.K_DOWN

# World
GROUND_Y     = 585
cam_y_global = 0   # horizontal camera only; y is fixed

# Colors
WHITE   = (255, 255, 255)
BLACK   = (  0,   0,   0)
FOX_OR  = (212,  98,  30)
BELLY_C = (240, 215, 165)
PAW_C   = ( 55,  18,   4)
EAR_PK  = (255, 155, 155)
SKY_T   = (130, 192, 240)
SKY_B   = (200, 228, 255)
SNOW_W  = (228, 240, 255)
SNOW_S  = (170, 205, 235)
PLAT_T  = (218, 234, 255)
PLAT_B  = ( 95, 138, 182)
PLAT_E  = ( 70, 110, 155)
CAVE_BG = ( 20,  12,   6)
CAVE_MD = ( 38,  22,  10)
CAVE_LT = ( 55,  32,  14)
CAVE_PT = ( 65,  40,  18)
CAVE_PE = ( 40,  24,  10)
LAVA_O  = (255,  80,   0)
LAVA_R  = (220,  30,   0)
LAVA_Y  = (255, 200,  40)
GOLD    = (255, 210,  50)
ICE_BL  = (155, 225, 255)
COIN_Y  = (255, 200,  30)
BEAR_W  = (242, 218, 165)
BEAR_S  = (198, 162, 108)
HUMAN_C = (180, 120,  70)
COAT_BR = ( 90,  55,  20)
SPIKE_G = (155, 155, 170)
SPIKE_L = (195, 195, 210)
NET_BR  = (110,  80,  25)

# Fonts
def _font(size, bold=False):
    for name in ('Georgia', 'Palatino Linotype', 'Book Antiqua', None):
        try:
            if name:
                return pygame.font.SysFont(name, size, bold=bold)
        except:
            pass
    return pygame.font.Font(None, int(size * 1.35))

FONT_XL = _font(60, True)
FONT_LG = _font(40, True)
FONT_MD = _font(28, True)
FONT_SM = _font(20)
FONT_XS = _font(15)

# Helpers
def dk(c, a=25):  return tuple(max(0, v - a) for v in c[:3])
def lt(c, a=25):  return tuple(min(255, v + a) for v in c[:3])

def txt(surf, text, font, color, cx, cy, shadow=True):
    if shadow:
        s = font.render(text, True, (0, 0, 0))
        surf.blit(s, (cx - s.get_width()//2 + 2, cy - s.get_height()//2 + 2))
    r = font.render(text, True, color)
    surf.blit(r, (cx - r.get_width()//2, cy - r.get_height()//2))

def draw_rounded_rect(surf, color, rect, radius=8, border=0, border_color=BLACK):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border:
        pygame.draw.rect(surf, border_color, rect, border, border_radius=radius)

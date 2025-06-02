import pygame
import numpy as np

pygame.init()

surface = pygame.Surface((128, 64))
surface.fill((0, 0, 0))
pygame.draw.circle(surface, (255, 255, 255), (0, 0), 10)
rgb = pygame.surfarray.array3d(surface)

binary = np.where(rgb.sum(axis=2) > 0, 1, 0)
bitmap = binary.T.tolist()
print(bitmap)

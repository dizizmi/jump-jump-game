import pygame
from pygame.locals import  *
from pygame import mixer
import pickle
from os import path

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

clock = pygame.time.Clock()
fps = 60

screen_width = 1000
screen_height = 1000

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Platformer')

#define fonts
font = pygame.font.SysFont('Bauhaus 93', 70)
font_score = pygame.font.SysFont('Bauhaus 93', 30)

#define game variables 
tile_size = 50
game_over = 0
main_menu = True
level = 0
max_levels = 7
score = 0

#define colors
white = (255,255,255)
blue = (0,0, 255)

#load image
sun_img =  pygame.image.load('assets/sun_img.png')
bg_img = pygame.image.load('assets/bg.png')
restart_img = pygame.image.load('assets/restart_btn.png')
start_img = pygame.image.load('assets/start_btn.png')
exit_img = pygame.image.load('assets/exit_btn.png')

#load sounds
pygame.mixer.music.load('assets/music.wav')
pygame.mixer.music.play(-1,0.0, 5000)
coin_fx = pygame.mixer.Sound('assets/coin.wav')
coin_fx.set_volume(0.5)
jump_fx = pygame.mixer.Sound('assets/jump.wav')
jump_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound('assets/gameover.wav')
game_over_fx.set_volume(0.5)

def draw_text(text, font, text_col, x , y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x,y))

#to reset level
def reset_level(level):
    player.reset(100, screen_height - 130) 
    spike_group.empty()
    enemy_group.empty()
    exit_group.empty()
#load in level data and create world
    if path.exists(f'level{level}_data'):
        pickle_in = open(f'level{level}_data', 'rb')
        world_data = pickle.load(pickle_in)

    world = World(world_data)
    
    return world


class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        action = False
         #get mouse position
        pos = pygame.mouse.get_pos()

        #check mouseover and clicked condition
        if self.rect.collidepoint(pos):
            #left button
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True
            
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        screen.blit(self.image, self.rect)

        return action

    





class Player():
    def __init__(self, x , y):
       self.reset(x,y)

    def update(self, game_over):
        dx = 0
        dy = 0
        #slow down images
        walk_cooldown = 10

        if game_over == 0:


            #get keypresses
            key = pygame.key.get_pressed()
            if key[pygame.K_SPACE] and self.jumped == False and self.in_air == False:
                jump_fx.play()
                self.vel_y = -15
                self.jumped = True
            if key[pygame.K_SPACE] == False:
                self.jumped = False

            #moving left and right
            if key[pygame.K_LEFT]:
                dx -= 5
                self.counter += 1
                self.direction = -1
            if key[pygame.K_RIGHT]:
                dx += 5
                self.counter += 1
                self.direction = 1
            #if left right button not pressed, allow the character image to be stationary -guy1
            if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False:
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]


            

            #handle animation, go thru the list of images, ref cooldown to slow down animation
            self.counter += 1
            #once counter reaches 20, resets to 0
            if self.counter > walk_cooldown: 
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            #add gravity
            self.vel_y += 1 
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y 

            #check for collision
            self.in_air = True
            for tile in world.tile_list:
                #check for collision in x direction
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0

            #check for collision in y direction
                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    #check if below ground like jumping
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    #check if above ground like falling
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False

            #check for collision with enemies
            if pygame.sprite.spritecollide(self, enemy_group, False):
                game_over = -1
                game_over_fx.play()
            
            #check for collision with spike
            if pygame.sprite.spritecollide(self, spike_group, False):
                game_over = -1
                game_over_fx.play()

            #check collision with exit door
            if pygame.sprite.spritecollide(self, exit_group, False):
                game_over = 1
            




            #update player coordinates
            self.rect.x += dx
            self.rect.y += dy

        elif game_over == -1:
            self.image = self.dead_image
            draw_text('GAME OVER!', font, blue, (screen_width // 2)-200, screen_height //2 )
            self.rect.y += 5
        #draw player onto screen
        screen.blit(self.image, self.rect)
        #lineweight onto character
        pygame.draw.rect(screen, (255, 255,255, 255), self.rect, 2)

        return game_over

    def reset(self,x,y):
        self.images_right = []
        self.images_left = []
        #track index from list
        self.index = 0
        self.counter = 0
        #going through 4 movements of character, " f'{}' " captures all 4 images
        for num in range(1,5):
            img_right = pygame.image.load(f'assets/guy{num}.png')
            img_right = pygame.transform.scale(img_right, (40, 80)) 
            #flip right image for a left image
            img_left = pygame.transform.flip(img_right, True, False)

            self.images_right.append(img_right)
            self.images_left.append(img_left)

        self.dead_image = pygame.image.load('assets/dead.png')
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air =  True

class World():
    def __init__(self,data):
        #adding as tuple
        self.tile_list = []
        #load images
        dirt_img = pygame.image.load('assets/dirt.png')
        grass_img = pygame.image.load('assets/grass.png')

        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    #adding as tuple, adding tiles and coordinates into 1
                    self.tile_list.append(tile)
                if tile == 2:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    #adding as tuple, adding tiles and coordinates into 1
                    self.tile_list.append(tile)

                if tile == 3:
                    enemy = Enemy(col_count * tile_size, row_count * tile_size -10)
                    enemy_group.add(enemy)
                
                if tile == 4:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0)
                    platform_group.add(platform)
                
                if tile == 5:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1)
                    platform_group.add(platform)
                
                if tile == 6:
                    spike = Spike(col_count * tile_size, row_count * tile_size + (tile_size // 2))
                    spike_group.add(spike)
                
                if tile == 7:
                    coin = Coin(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
                    coin_group.add(coin)

                if tile == 8:
                    exit =  Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    exit_group.add(exit)

                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])
            pygame.draw.rect(screen, (255,255,255), tile[1], 2)

class Enemy(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('assets/enemy.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        #moving left, since it hits 51, minus 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1

class Platform(pygame.sprite.Sprite):
    def __init__(self,x,y, move_x, move_y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('assets/tile_0393.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size //2 ))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_counter = 0
        self.move_direction = 1
        self.move_x = move_x
        self.move_y = move_y
     
    def update(self):
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        #moving left, since it hits 51, minus 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1

class Spike(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('assets/spike.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Coin(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('assets/carrots.png')
        self.image = pygame.transform.scale(img, (tile_size // 2, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        #creating x y center pts

class Exit(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('assets/exit.png')
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

#player is 80px tall, tile is 50px
player = Player(100, screen_height - 130) 
enemy_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
spike_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

#load in level data and create world
if path.exists(f'level{level}_data'):
    pickle_in = open(f'level{level}_data', 'rb')
    world_data = pickle.load(pickle_in)

world = World(world_data)

#create buttons
restart_button = Button(screen_width // 2 - 50, screen_height // 2 + 100, restart_img)
start_button = Button(screen_width // 2 -150 , screen_height // 2 -200 , start_img)
exit_button = Button(screen_width // 2 -130, screen_height // 2 -50, exit_img)

run = True
while run:

    clock.tick(fps)
    
    screen.blit(bg_img, (0,0))
    screen.blit(sun_img, (100,100))

    if main_menu == True: 
        if exit_button.draw():
            run = False
        if start_button.draw():
            main_menu = False
    else: 
        world.draw()

        if game_over == 0:
        #can draw sprite methods
            enemy_group.update()
            platform_group.update()
            #update score

            if pygame.sprite.spritecollide(player, coin_group, True):
                score += 1
                coin_fx.play()
            draw_text('X ' + str(score), font_score, white, tile_size -10, 10)
        
        enemy_group.draw(screen) 
        platform_group.draw(screen)
        spike_group.draw(screen)
        coin_group.draw(screen)
        exit_group.draw(screen)

        game_over = player.update(game_over)
    #score image
    score_coin = Coin(tile_size // 2, tile_size //2 )
    coin_group.add(score_coin)

    #character died
    if game_over == -1:
        if restart_button.draw():
            world_data = []
            world = reset_level(level)
            game_over = 0

    #completed level
    if game_over == 1:
        #reset game to next level
        level += 1
        if level <= max_levels:
            #reset level
            #empty world data
            world_data = []
            world = reset_level(level)
            game_over = 0
        else:
            draw_text('YOU WIN!', font, blue, (screen_width //2)-140, screen_height // 2)
            #restart level
            if restart_button.draw():
                level = 1
                #reset level
                world_data = []
                world = reset_level(level)
                game_over = 0


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()


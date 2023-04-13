import datetime
import os
import random
import string

import pygame
import RPi.GPIO as GPIO
import json
import time

######################################### Settings for the User ###############################################
HIGHSCORES_FILE = 'highscores.json'  # name of the file for the highscores
MAX_HIGHSCORES = 10000  # how many highscores should be displayed (watch out for screen size)
TIMER_MAX_DURATION = 10 * 60  # how long until timer runs out x * 60seconds
SPEAKER_VOLUME = 1  # doesn't seem to change anything in the current hardware configuration
ENTER_NAME_TEXT = "Gib deinen Namen ein:"
###############################################################################################################

# Constants
REL_MENU_TITLE_Y = 0.046
REL_HIGHSCORES_Y = 0.139
DEBOUNCE_DELAY = 0.5
BUZZER_EVENT = pygame.USEREVENT + 1

# Initialize GPIO
GPIO_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize Speaker
pygame.mixer.init()
pygame.mixer.music.set_volume(SPEAKER_VOLUME)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BACKGROUND_COLOR = BLACK
TEXT_COLOR = WHITE

# Font settings
pygame.font.init()
FONT_TIMER = pygame.font.Font(None, 400)
FONT_TIME = pygame.font.Font(None, 200)
FONT_BIG_PLUS = pygame.font.Font(None, 150)
FONT_BIG = pygame.font.Font(None, 100)
FONT_MEDIUM_PLUS = pygame.font.Font(None, 50)
FONT_MEDIUM = pygame.font.Font(None, 36)
FONT_SMALL = pygame.font.Font(None, 24)

# Screen dimensions
pygame.init()
info = pygame.display.Info()
WIDTH = info.current_w
HEIGHT = info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)


# Highscore functions
def load_highscores():
    if not os.path.exists(HIGHSCORES_FILE):
        return []

    with open(HIGHSCORES_FILE, 'r') as file:
        highscores = json.load(file)
    return highscores


def save_highscores(highscores):
    with open(HIGHSCORES_FILE, 'w') as file:
        json.dump(highscores, file, indent=4)


def add_highscore(new_name, new_time):
    highscores = load_highscores()
    new_name = new_name.upper()

    # Check if the name already exists
    if any(hs['name'] == new_name for hs in highscores):
        return

    minutes, seconds = divmod(new_time, 60)
    ms = (new_time - int(new_time)) * 100
    formatted_time = f"{int(minutes):02d}:{int(seconds):02d}:{int(ms):02d}"
    highscores.append({'name': new_name, 'time': formatted_time})
    highscores.sort(key=lambda x: x['time'])
    save_highscores(highscores)


def name_exists(name, highscores):
    for highscore in highscores:
        if highscore['name'] == name:
            return True
    return False


def generate_code(length):
    return ''.join(random.choices(string.ascii_uppercase, k=length))


def play_sound(num):
    sound = pygame.mixer.Sound(f"sounds/example{num}.wav")
    sound.play()


def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, 1, color)
    text_rect = text_obj.get_rect()
    text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)


def draw_main_menu(highscores, scroll_offset):
    screen.fill(BLACK)

    for i, highscore in enumerate(highscores[:MAX_HIGHSCORES]):
        name = highscore['name']
        score = highscore['time']
        entry_text = f"{i + 1}. {name} - {score}"
        entry_obj = FONT_BIG.render(entry_text, 1, WHITE)

        entry_rect = entry_obj.get_rect(centerx=WIDTH // 2, y=int(HEIGHT * REL_HIGHSCORES_Y) + (i + 0.5) * 70 - scroll_offset)
        screen.blit(entry_obj, entry_rect)

    pygame.draw.rect(screen, (0, 0, 0), (0, 0, WIDTH, FONT_BIG_PLUS.get_height() + 50))
    title_text = "BESTENLISTE"
    title_obj = FONT_BIG_PLUS.render(title_text, 1, WHITE)
    title_rect = title_obj.get_rect(centerx=WIDTH // 2, y=int(HEIGHT * REL_MENU_TITLE_Y))
    screen.blit(title_obj, title_rect)
    pygame.display.flip()


def scroll_highscores(event, scroll_offset):
    if event.key == pygame.K_UP:
        scroll_offset += 70
    elif event.key == pygame.K_DOWN:
        scroll_offset -= 70
    return scroll_offset


def draw_timer(timer_value):
    screen.fill(BACKGROUND_COLOR)
    minutes, seconds = divmod(timer_value, 60)
    milliseconds = (timer_value % 1) * 1000
    timer_text = f"{int(minutes):02d}:{int(seconds):02d}:{int(milliseconds):03d}"
    text_obj = FONT_TIMER.render(timer_text, 1, TEXT_COLOR)
    text_rect = text_obj.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text_obj, text_rect)
    pygame.display.flip()


def draw_name_input(name, timer_value_formatted, cursor_visible):
    screen.fill(BACKGROUND_COLOR)

    # Center the "Your time" text
    your_time_text = f"Deine Zeit: {timer_value_formatted}"
    your_time_obj = FONT_TIME.render(your_time_text, 1, TEXT_COLOR)
    your_time_rect = your_time_obj.get_rect(centerx=WIDTH // 2, y=HEIGHT // 2 - 250)
    screen.blit(your_time_obj, your_time_rect)

    # Center the "Enter your name" text
    enter_your_name_text = ENTER_NAME_TEXT
    enter_your_name_obj = FONT_BIG.render(enter_your_name_text, 1, TEXT_COLOR)
    enter_your_name_rect = enter_your_name_obj.get_rect(centerx=WIDTH // 2, y=HEIGHT // 2 - 100)
    screen.blit(enter_your_name_obj, enter_your_name_rect)

    # Center the name input text
    name_obj = FONT_BIG.render(name, 1, TEXT_COLOR)
    name_rect = name_obj.get_rect(centerx=WIDTH // 2, y=HEIGHT // 2)
    screen.blit(name_obj, name_rect)

    # Calculate the desired width of the rectangle (12 letters wide)
    letter_width, _ = FONT_BIG.size("A")
    desired_width = letter_width * 12

    # Calculate the left edge of the centered rectangle
    rect_left = (WIDTH - desired_width) // 2

    # Draw the field around the name input
    pygame.draw.rect(screen, TEXT_COLOR,
                     (rect_left - 5, name_rect.y - 5, desired_width, name_rect.height + 10), 2)

    # Draw cursor
    if cursor_visible:
        cursor_pos = FONT_BIG.size(name)[0]
        pygame.draw.line(screen, TEXT_COLOR, (name_rect.x + cursor_pos, name_rect.y),
                         (name_rect.x + cursor_pos, name_rect.y + FONT_BIG.get_height()), 3)

    pygame.display.flip()


def draw_error_screen():
    screen.fill(BACKGROUND_COLOR)

    # Center the "Timer exceeded the maximum duration" text
    error_message = "Leider hat es nicht gereicht :("
    error_message_obj = FONT_TIME.render(error_message, 1, TEXT_COLOR)
    error_message_rect = error_message_obj.get_rect(centerx=WIDTH // 2, y=HEIGHT // 2 - 100)
    screen.blit(error_message_obj, error_message_rect)

    # Center the "Press SPACE to return to the main menu" text
    sub_message = "Drücke den Buzzer um zurückzukehren"
    sub_message_obj = FONT_BIG_PLUS.render(sub_message, 1, TEXT_COLOR)
    sub_message_rect = sub_message_obj.get_rect(centerx=WIDTH // 2,
                                                y=error_message_rect.y + error_message_rect.height + 20)
    screen.blit(sub_message_obj, sub_message_rect)

    pygame.display.flip()


def main():
    # Initial setup
    highscores = load_highscores()
    state = 'menu'
    timer_started = False
    timer_start_time = 0
    timer_value = 0
    name = ""
    name_error = False
    cursor_visible = True
    cursor_timer = datetime.datetime.now()
    scroll_offset = 0
    last_buzzer_press_time = time.time()
    running = True
    # Main loop
    while running:
        current_time = time.time()
        if (current_time - last_buzzer_press_time) > DEBOUNCE_DELAY and not GPIO.input(GPIO_PIN):
            pygame.event.post(pygame.event.Event(BUZZER_EVENT))
            last_buzzer_press_time = current_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN or event.type == BUZZER_EVENT:
                if event.type == pygame.KEYDOWN:
                    key = event.key
                else:
                    key = pygame.K_SPACE
                if key == pygame.K_ESCAPE:
                    running = False
                if state == 'name_input':
                    if key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    elif key == pygame.K_SPACE and name.strip() == "":
                        name = generate_code(6)
                        name = name.upper()
                    elif key == pygame.K_SPACE:
                        if name_exists(name, highscores):
                            name_error = True
                        else:
                            add_highscore(name, timer_value)
                            highscores = load_highscores()
                            state = 'menu'
                            name = ""
                            name_error = False
                    elif key is not None and key not in (pygame.K_SPACE, pygame.K_TAB):
                        name += event.unicode
                elif key == pygame.K_SPACE:
                    if state == 'menu':
                        state = 'timer'
                        timer_started = True
                        timer_start_time = time.time()
                    elif state == 'timer':
                        play_sound(2)
                        state = 'name_input'
                        timer_started = False
                        timer_value = time.time() - timer_start_time
                        minutes, seconds = divmod(timer_value, 60)
                        ms = (timer_value - int(timer_value)) * 100
                        timer_value_formatted = f"{int(minutes):02d}:{int(seconds):02d}:{int(ms):02d}"
                    elif state == 'error':
                        state = 'menu'
                elif state == 'menu' and event.type == pygame.KEYDOWN:
                    scroll_offset = scroll_highscores(event, scroll_offset)
        if state == 'menu':
            draw_main_menu(highscores, scroll_offset)
        elif state == 'timer':
            draw_timer(timer_value)
        elif state == 'name_input':
            now = datetime.datetime.now()
            if (now - cursor_timer).microseconds >= 500000:
                cursor_timer = now
                cursor_visible = not cursor_visible
            draw_name_input(name, timer_value_formatted, cursor_visible)
            if name_error:
                draw_text("Name already exists, enter another name", FONT_SMALL, TEXT_COLOR, screen, WIDTH // 2 - 250,
                          HEIGHT // 2 + 50)
                pygame.display.flip()
        if timer_started:
            timer_value = time.time() - timer_start_time
            if timer_value >= TIMER_MAX_DURATION:
                timer_started = False
                state = 'error'
        if state == 'error':
            draw_error_screen()
        pygame.display.flip()
        time.sleep(0.01)

    pygame.quit()


if __name__ == "__main__":
    main()

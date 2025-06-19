_author_='WenAlis'
# main.py
import pygame
import os
import random
from settings import * # 导入所有设置
from sprites import Player, Wall, Coin, Monster, Button, Door, Merchant,Bomb, Explosion, BreakableWall, HealthPotion, AttackPotion,Switch,TalismanPickup,Boss


# YELLOW 定义移到这里，确保全局可用
if not hasattr(pygame.colordict, 'YELLOW'):
    YELLOW = (255,255,0)
else:
    YELLOW = pygame.colordict.THECOLORS['yellow']

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("V.Klinge(Beta)") 
        self.clock = pygame.time.Clock()
        self.running = True
        self.all_sprites = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.coins_group = pygame.sprite.Group()
        self.monsters_group = pygame.sprite.Group()
        self.buttons_group = pygame.sprite.Group()
        self.doors_group = pygame.sprite.Group()
        self.merchants_group = pygame.sprite.Group()
        self.bombs_group = pygame.sprite.Group()
        self.effects_group = pygame.sprite.Group()
        self.breakable_walls_group = pygame.sprite.Group()
        self.potions_group = pygame.sprite.Group()
        self.switches_group = pygame.sprite.Group()
        self.talisman_pickups_group = pygame.sprite.Group()

        self.current_game_state = STATE_MENU
        self.current_interacting_merchant = None
        self.current_interacting_player = None
        self.total_spent_at_merchant1 = 0
        self.merchant2_switch_spawned = False
        self.adv_merchant_unlocked = False
        self.boss_entity = None # <--- 新增：用于存储BOSS实例
        self.is_boss_active = False # <--- 新增：标记BOSS战是否激活
        try:
            self.font = pygame.font.SysFont("arial", 30)
            self.large_font = pygame.font.SysFont("arial", 48)
            self.title_font = pygame.font.SysFont("arial", 72) # 如果封面需要特定标题字体
            print(f"Loaded system font 'arial' (or fallback).")
        except pygame.error as e:
            print(f"Pygame SysFont error: {e}. Using Pygame default font.")
            self.font = pygame.font.SysFont(None, 30)
            self.large_font = pygame.font.SysFont(None, 48)
            self.title_font = pygame.font.SysFont(None, 72) # 对应的fallback

        self.cover_background_img = None
        if COVER_BACKGROUND_IMG_NAME:
            try:
                self.cover_background_img = load_image(COVER_BACKGROUND_IMG_NAME, scale_to_grid=False)
                if self.cover_background_img.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
                    self.cover_background_img = pygame.transform.scale(self.cover_background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                print(f"封面背景 '{COVER_BACKGROUND_IMG_NAME}' 加载成功。")
            except Exception as e:
                print(f"错误：无法加载封面背景图片 '{COVER_BACKGROUND_IMG_NAME}'. 错误: {e}")
                self.cover_background_img = None
        
        # --- 玩家1 定义和创建 ---
        self.player1_controls = {
            'up': pygame.K_w, 'down': pygame.K_s, 'left': pygame.K_a, 'right': pygame.K_d,
            'interact': INTERACTION_KEY, 'bomb': BOMB_PLACE_KEY_P1
        }
        self.player1 = Player(self, PLAYER_1_START_GRID_X, PLAYER_1_START_GRID_Y, PLAYER_IMG_NAME_1, self.player1_controls)

        # --- 玩家2 定义和创建 ---
        self.player2_controls = {
            'up': pygame.K_UP, 'down': pygame.K_DOWN, 'left': pygame.K_LEFT, 'right': pygame.K_RIGHT,
            'interact': INTERACTION_KEY, 'bomb': BOMB_PLACE_KEY_P2
        }
        self.player2 = Player(self, PLAYER_2_START_GRID_X, PLAYER_2_START_GRID_Y, PLAYER_IMG_NAME_2, self.player2_controls)

    def initialize_game_world(self):
        """初始化或重置游戏世界状态，用于开始新游戏"""
        print("Initializing game world...")
        # 清理可能存在的旧精灵 (如果从游戏结束回到菜单再开始新游戏)
        self.all_sprites.empty()
        self.walls.empty()
        self.coins_group.empty()
        self.monsters_group.empty()
        self.buttons_group.empty()
        self.doors_group.empty()
        self.merchants_group.empty() # 清空商人组，确保高级商人不会残留
        self.bombs_group.empty()
        self.effects_group.empty()
        self.breakable_walls_group.empty()
        self.potions_group.empty()
        self.switches_group.empty()
        self.talisman_pickups_group.empty()
        self.boss_entity = None # <--- 重置BOSS实例
        self.is_boss_active = False # <--- 重置BOSS战标记

        # 重置玩家状态 (位置、生命、金币、符文效果等)
        # 注意：Player对象在__init__中已创建，这里是重置其属性
        # 或者，你也可以选择在 initialize_game_world 中重新创建 Player 对象
        self.player1.reset_state(PLAYER_1_START_GRID_X, PLAYER_1_START_GRID_Y) # 假设 Player 有 reset_state 方法
        self.all_sprites.add(self.player1)

        self.player2.reset_state(PLAYER_2_START_GRID_X, PLAYER_2_START_GRID_Y) # 假设 Player 有 reset_state 方法
        self.all_sprites.add(self.player2)

        # 重置游戏进程相关变量
        self.current_interacting_merchant = None
        self.current_interacting_player = None
        self.total_spent_at_merchant1 = 0
        self.merchant2_switch_spawned = False
        self.adv_merchant_unlocked = False # 每次开始新游戏，高级商人需要重新解锁

        self.load_map_data() # 加载当前关卡的地图数据
        print("Game world initialized.")
        
    def draw_menu(self):
        """绘制游戏封面/主菜单"""
        # 绘制背景
        if self.cover_background_img:
            self.screen.blit(self.cover_background_img, (0,0))
        else:
            self.screen.fill(DARK_GREY) # 如果没有背景图，用深灰色填充

           
    def load_map_data(self):
        """从一个简单的数据结构加载地图并创建墙壁对象"""
        # 'H' 代表生命药水, 'A' 代表攻击药水
        self.map_layout = [
            "1111111111111111",
            "10C0MC0MC0C01M01",
            "1011100111M010C1", 
            "1CM00C01M00100C1",
            "11111100MC010001",
            "1HAMHD0MM1M00MC1", 
            "1CMAC10C0B1C10C1", 
            "11W11100C1C10001",
            "1TW1M01M00M0C011",
            "1TT100C0MC00C001",
            "1T10M0S0CC0M0M01",
            "11111111111111W1",
        ]
        # 简单的刷新点安全检查 (可选但推荐)
        if self.map_layout[PLAYER_1_START_GRID_Y][PLAYER_1_START_GRID_X] == '1':
            print(f"警告：玩家1的初始位置 ({PLAYER_1_START_GRID_X}, {PLAYER_1_START_GRID_Y}) 在墙上！请修改settings.py或地图。")
            # 在这里你可以选择抛出错误，或者将玩家移动到一个默认的安全位置
            # 为简单起见，我们只打印警告

        # 如果你启用了玩家2，也做类似的检查
        if hasattr(self, 'player2'):
            if self.map_layout[PLAYER_2_START_GRID_Y][PLAYER_2_START_GRID_X] == '1':
                print(f"警告：玩家2的初始位置 ({PLAYER_2_START_GRID_X}, {PLAYER_2_START_GRID_Y}) 在墙上！")


        for row_index, row_data in enumerate(self.map_layout):
            for col_index, tile_char in enumerate(row_data):
                if tile_char == '1':
                    wall = Wall(self, col_index, row_index)
                    self.all_sprites.add(wall)
                    self.walls.add(wall)
                elif tile_char == 'C': # 如果是金币
                    coin = Coin(self, col_index, row_index)
                    self.all_sprites.add(coin)
                    self.coins_group.add(coin) # 将金币也加入金币专属组
                elif tile_char == 'M': # 如果是怪物
                    monster = Monster(self, col_index, row_index, MONSTER_SLIME_IMG_NAME)
                    self.all_sprites.add(monster)
                    self.monsters_group.add(monster) # 加入怪物专属组
                elif tile_char == 'B': # 创建按钮
                    # 按钮和门通过 pair_id 关联，这里我们使用 settings 中的全局 ID
                    button = Button(self, col_index, row_index, BUTTON_DOOR_PAIR_ID)
                    self.all_sprites.add(button) # 按钮会被绘制
                    self.buttons_group.add(button)
                elif tile_char == 'D': # 创建门
                    door = Door(self, col_index, row_index, BUTTON_DOOR_PAIR_ID)
                    self.all_sprites.add(door) # 门也会被绘制（可能是透明的）
                    self.doors_group.add(door)
                    # 初始时，如果门是关闭的并且应该像墙一样，则加入walls组
                    if not door.is_open and door.is_wall_when_closed:
                        self.walls.add(door)
                elif tile_char == 'S': # 创建普通商人
                    merchant = Merchant(self, col_index, row_index, MERCHANT_NORMAL_IMG_NAME, "normal")
                    self.all_sprites.add(merchant)
                    self.merchants_group.add(merchant)
                elif tile_char == 'W': # 创建可破坏的墙
                    b_wall = BreakableWall(self, col_index, row_index)
                    self.all_sprites.add(b_wall)
                    self.walls.add(b_wall) # 可破坏的墙初始也是墙，会阻挡
                    self.breakable_walls_group.add(b_wall) # 加入专门的组用于被炸弹检测
                elif tile_char == 'H': # 创建生命药水
                    health_potion = HealthPotion(self, col_index, row_index)
                    self.all_sprites.add(health_potion)
                    self.potions_group.add(health_potion) # 加入药水专属组
                elif tile_char == 'A': # 创建攻击药水
                    attack_potion = AttackPotion(self, col_index, row_index)
                    self.all_sprites.add(attack_potion)
                    self.potions_group.add(attack_potion)
                elif tile_char == 'T': # <--- 新增对符箓拾取物的处理
                    talisman_pickup = TalismanPickup(self, col_index, row_index)
                    self.all_sprites.add(talisman_pickup)
                    self.talisman_pickups_group.add(talisman_pickup) # 加入专门的符箓组
                elif tile_char == 'P': # 创建传送门
                    # 假设这个传送门也由 pair_id=BUTTON_DOOR_PAIR_ID 的按钮控制使其“打开”（消失）
                    # 或者你可以为传送门设置一个独立的pair_id，由地图上特定的“传送门激活器”控制
                    # 或者它初始就是打开的，或者由炸弹炸开（如果它是一个可破坏墙壁后面的空间）
                    portal_door = Door(self, col_index, row_index, BUTTON_DOOR_PAIR_ID, is_portal=True)
                    # 示例：让传送门初始也是关闭的，需要按钮打开才能传送
                    self.all_sprites.add(portal_door); self.doors_group.add(portal_door)
                    if not portal_door.is_open and portal_door.is_wall_when_closed:
                        self.walls.add(portal_door)
                    # 如果你想让传送门初始就是“打开”且可传送的，可以：
                    # portal_door.set_state(True) # 这样它就直接是透明且无碰撞的

    # ... (notify_door, spawn_switch_for_adv_merchant, spawn_monsters_for_switch, event_switch_fully_activated, run, events, attempt_purchase_item, update, draw_* 方法基本不变) ...

    # --- 新增：处理关卡切换的方法 (占位符) ---
    def trigger_level_transition(self):
        print("关卡切换被触发！正在准备进入下一关...")
        # 在这里，以后你会添加加载新地图数据、重置玩家位置等逻辑
        # 例如:
        # self.current_level_index += 1
        # self.load_map_data_for_level(self.current_level_index)
        # self.player1.reset_position(new_start_x, new_start_y)
        # self.player2.reset_position(new_start_x, new_start_y)
        # 清理当前关卡的特定精灵（怪物、某些物品等）
        # self.monsters_group.empty()
        # self.all_sprites.remove(*self.monsters_group) # 从all_sprites也移除
        # ...等等


    def notify_door(self, pair_id, is_button_pressed):
        """当按钮状态改变时，更新对应ID的门的状态"""
        for door in self.doors_group:
            if door.pair_id == pair_id:
                door.set_state(is_button_pressed)

    # --- 新增方法 ---
    def spawn_switch_for_adv_merchant(self):
        """在预定位置生成用于解锁高级商人的开关"""
        if not self.merchant2_switch_spawned:
            # 检查目标位置是否为空（没有墙、没有其他固定障碍物）
            # 为简单起见，我们先假设settings中定义的SWITCH_SPAWN_GRID_X/Y是安全的
            print(f"消费达到阈值！在 ({SWITCH_SPAWN_GRID_X},{SWITCH_SPAWN_GRID_Y}) 生成了一个开关！")
            adv_switch = Switch(self, SWITCH_SPAWN_GRID_X, SWITCH_SPAWN_GRID_Y, ADV_MERCHANT_SWITCH_ID, 'off')
            self.all_sprites.add(adv_switch)
            self.switches_group.add(adv_switch)
            self.merchant2_switch_spawned = True

    def spawn_monsters_for_switch(self, switch_instance):
        """为一个开关生成特定的中等怪物""" # 修改注释
        print(f"DEBUG: spawn_monsters_for_switch called for switch {switch_instance.switch_id} at ({switch_instance.grid_x}, {switch_instance.grid_y})")

        monster_spawn_coords = [
            (switch_instance.grid_x, switch_instance.grid_y - 1), # 上
            (switch_instance.grid_x, switch_instance.grid_y + 1), # 下
            (switch_instance.grid_x - 1, switch_instance.grid_y), # 左
            (switch_instance.grid_x + 1, switch_instance.grid_y), # 右
        ]
        monsters_generated = 0
        print(f"DEBUG: Attempting to spawn MEDIUM monsters at: {monster_spawn_coords}")

        for gx, gy in monster_spawn_coords:
            print(f"DEBUG: Checking spawn coord for medium monster: ({gx}, {gy})")
            if 0 <= gx < SCREEN_WIDTH // GRID_SIZE and 0 <= gy < SCREEN_HEIGHT // GRID_SIZE:
                is_blocked = False
                for wall_like_object in self.walls:
                    if wall_like_object.grid_x == gx and wall_like_object.grid_y == gy:
                        is_blocked = True; break
                if not is_blocked:
                    for existing_monster in self.monsters_group: # 避免叠怪
                        if existing_monster.grid_x == gx and existing_monster.grid_y == gy:
                            is_blocked = True; break
                
                if not is_blocked:
                    print(f"DEBUG: Spawning MEDIUM monster at ({gx}, {gy}) for switch {switch_instance.switch_id}")
                    # --- 创建中等怪物实例 ---
                    # 我们需要一种方式让 Monster 类知道这些是中等怪的属性
                    # 方案1: Monster类构造函数接收属性 (如上面可选的修改)
                    # monster = Monster(self, gx, gy, MONSTER_MEDIUM_IMG_NAME,
                    #                   MONSTER_MEDIUM_HEALTH, MONSTER_MEDIUM_ATTACK_POWER, MONSTER_MEDIUM_GOLD_DROP,
                    #                   spawned_by_switch=switch_instance)

                    # 方案2: （更简单，如果Monster类没有修改构造函数）
                    # 我们直接在创建后修改其属性。这不太优雅，但可行。
                    # 或者，如果中等怪和小怪共享大部分逻辑，只是属性不同，
                    # 可以在 Monster.__init__ 中根据传入的 image_filename 来决定属性。
                    # 为了简单，我们先假设 MONSTER_MEDIUM_IMG_NAME 会被 Monster 类识别并自动应用不同属性（这需要修改Monster类）
                    # 或者我们创建一个新的 MediumMonster 类继承自 Monster。

                    # --- 目前最直接的修改方式 (不改Monster类构造函数): ---
                    # 创建一个 Monster 对象，然后手动覆盖其属性
                    monster = Monster(self, gx, gy, MONSTER_MEDIUM_IMG_NAME, spawned_by_switch=switch_instance)
                    monster.health = MONSTER_MEDIUM_HEALTH
                    monster.attack_power = MONSTER_MEDIUM_ATTACK_POWER
                    monster.gold_value = MONSTER_MEDIUM_GOLD_DROP
                    # 你可能还需要一个 monster.type = "medium" 标志，如果其他逻辑需要区分

                    self.all_sprites.add(monster)
                    self.monsters_group.add(monster)
                    switch_instance.linked_monsters.add(monster)
                    monsters_generated += 1
                else:
                    print(f"DEBUG: Coord ({gx}, {gy}) was blocked, medium monster not spawned.")
            else:
                print(f"DEBUG: Coord ({gx}, {gy}) is out of screen bounds for medium monster.")

        switch_instance.monsters_to_defeat_count = monsters_generated
        print(f"DEBUG: Total medium monsters generated for switch: {monsters_generated}")
        if monsters_generated == 0 and switch_instance.state == 'pending_monsters':
            print("警告：未能为开关生成任何中等怪物，开关将直接激活。")
            switch_instance.activate_fully()
    def spawn_final_boss(self):
        """生成最终BOSS"""
        if self.boss_entity and self.boss_entity.alive(): # 防止重复生成
            print("BOSS已存在！")
            return

        print(f"准备在 ({BOSS_SPAWN_GRID_X}, {BOSS_SPAWN_GRID_Y}) 生成最终BOSS...")
        # (可选) 清理当前地图上的其他怪物或元素，为BOSS战做准备
        # for monster in self.monsters_group:
        #     monster.kill()
        
        self.boss_entity = Boss(self, BOSS_SPAWN_GRID_X, BOSS_SPAWN_GRID_Y, BOSS_FINAL_IMG_NAME)
        self.all_sprites.add(self.boss_entity)
        self.monsters_group.add(self.boss_entity) # BOSS也是一种怪物，会被攻击逻辑处理
        self.is_boss_active = True # <--- BOSS生成后，标记BOSS战开始
        print("BOSS战已激活！")
        # (可选) 播放BOSS出场音乐/音效
        # pygame.mixer.music.load('path_to_boss_music.mp3')
        # pygame.mixer.music.play(-1)
    def draw_game_won_screen(self):
        """绘制游戏胜利/结束界面"""
        self.screen.fill(DARK_GREY) # 或者用一个特殊的胜利背景图

        # 胜利标题
        title_text = "YOU WON!"
        title_surf = self.title_font.render(title_text, True, YELLOW) # 假设有 self.title_font
        title_rect = title_surf.get_rect(centerx=SCREEN_WIDTH / 2, centery=SCREEN_HEIGHT / 3)
        self.screen.blit(title_surf, title_rect)

        # 感谢信息或下一步提示
        msg1_text = "Congratulations! You have defeated the final boss."
        msg1_surf = self.large_font.render(msg1_text, True, WHITE)
        msg1_rect = msg1_surf.get_rect(centerx=SCREEN_WIDTH / 2, centery=title_rect.bottom + 50)
        self.screen.blit(msg1_surf, msg1_rect)
        
        msg2_text = "Thanks for playing V.Klinge (Beta)!"
        msg2_surf = self.font.render(msg2_text, True, WHITE)
        msg2_rect = msg2_surf.get_rect(centerx=SCREEN_WIDTH / 2, centery=msg1_rect.bottom + 40)
        self.screen.blit(msg2_surf, msg2_rect)

        # 返回主菜单或退出游戏的提示
        prompt_text = "Press ENTER to return to Menu, or ESC to Exit."
        prompt_surf = self.font.render(prompt_text, True, LIGHT_GREY)
        prompt_rect = prompt_surf.get_rect(centerx=SCREEN_WIDTH / 2, bottom=SCREEN_HEIGHT - 50)
        self.screen.blit(prompt_surf, prompt_rect)

    def trigger_game_won(self):
        """当游戏胜利条件满足时调用 (例如BOSS被击败)"""
        if self.current_game_state != STATE_GAME_WON: # 确保只触发一次
            print("游戏胜利！切换到胜利界面...")
            self.current_game_state = STATE_GAME_WON
            pygame.display.set_caption("V.Klinge(Beta) - VICTORY!")
            # (可选) 停止BOSS音乐，播放胜利音乐
            # pygame.mixer.music.stop()
            # pygame.mixer.music.load('path_to_victory_music.mp3')
            # pygame.mixer.music.play()
    def trigger_game_over(self, message="英雄惜败，请重振旗鼓！"): # <--- 新增方法，接受一个可选的失败信息
        if self.current_game_state != STATE_GAME_OVER and self.current_game_state != STATE_GAME_WON: # 避免重复触发或在胜利后触发
            print(f"游戏结束！原因: {message}")
            self.current_game_state = STATE_GAME_OVER
            self.is_boss_active = False # <--- BOSS战（如果激活过）结束
            self.game_over_message = message # 存储失败信息以供显示
            pygame.display.set_caption("V.Klinge(Beta) - GAME OVER")
            # (可选) 播放失败音乐
            # pygame.mixer.music.stop()
            # pygame.mixer.music.load('path_to_gameover_music.mp3')
            # pygame.mixer.music.play()
    def draw_game_over_screen(self): # <--- 新增方法
        self.screen.fill((50, 0, 0)) # 深红色背景

        title_text = "GAME OVER" # 已经是英文
        # 确保 self.title_font 是有效的
        if hasattr(self, 'title_font') and self.title_font:
            title_surf = self.title_font.render(title_text, True, (150, 150, 150))
            title_rect = title_surf.get_rect(centerx=SCREEN_WIDTH / 2, centery=SCREEN_HEIGHT / 3)
            self.screen.blit(title_surf, title_rect)
        else:
            print("ERROR: self.title_font is not valid in draw_game_over_screen!")
            # 可以画一个备用文本或什么都不画
            title_rect = pygame.Rect(0, SCREEN_HEIGHT / 3, SCREEN_WIDTH, 50) # 创建一个虚拟rect以便后续定位


        # 获取并显示主要的 game_over_message
        main_message_text = getattr(self, 'game_over_message', "You have been defeated.") # 默认英文消息
        # 确保 self.large_font 是有效的
        if hasattr(self, 'large_font') and self.large_font:
            message_surf = self.large_font.render(main_message_text, True, WHITE)
            message_rect = message_surf.get_rect(centerx=SCREEN_WIDTH / 2, centery=title_rect.bottom + 60)
            self.screen.blit(message_surf, message_rect)
        else:
            print("ERROR: self.large_font is not valid in draw_game_over_screen!")
            message_rect = pygame.Rect(0, title_rect.bottom + 60, SCREEN_WIDTH, 40) # 虚拟rect

        # 根据 game_over_message 显示不同的英文嘲讽
        current_message = getattr(self, 'game_over_message', "")
        if "Both heroes have fallen" in current_message: # <--- 修改为英文判断条件
            taunt_text = "At least you perished together, right?"
        elif "Defeated. Try again" in current_message: # 可以为其他特定消息添加条件
            taunt_text = "The path ahead is treacherous. Gather your strength."
        else: # 通用嘲讽
            taunt_text = "Perhaps this maze is too challenging for you."
            
        # 确保 self.font 是有效的
        if hasattr(self, 'font') and self.font:
            taunt_surf = self.font.render(taunt_text, True, LIGHT_GREY)
            taunt_rect = taunt_surf.get_rect(centerx=SCREEN_WIDTH / 2, centery=message_rect.bottom + 40)
            self.screen.blit(taunt_surf, taunt_rect)
        else:
            print("ERROR: self.font is not valid in draw_game_over_screen!")

        prompt_text = "Press ENTER to return to Menu, or ESC to Exit." # 这个已经是英文了
        if hasattr(self, 'font') and self.font:
            prompt_surf = self.font.render(prompt_text, True, LIGHT_GREY)
            prompt_rect = prompt_surf.get_rect(centerx=SCREEN_WIDTH / 2, bottom=SCREEN_HEIGHT - 50)
            self.screen.blit(prompt_surf, prompt_rect)
    def event_switch_fully_activated(self, switch_instance):
        """当一个开关被完全激活时（所有关联怪物被击败）调用"""
        if switch_instance.switch_id == ADV_MERCHANT_SWITCH_ID:
            print("高级商人解锁开关已完全激活！高级商人条件满足！")
            self.adv_merchant_unlocked = True
            # --- 新增：生成高级商人 ---
            if not any(isinstance(sprite, Merchant) and sprite.merchant_type == "advanced" for sprite in self.merchants_group):
                # 检查是否已存在高级商人，避免重复生成
                print(f"尝试在 ({ADV_MERCHANT_SPAWN_GRID_X}, {ADV_MERCHANT_SPAWN_GRID_Y}) 生成高级商人。")
                # 首先检查目标位置是否合法且空闲
                can_spawn = True
                if not (0 <= ADV_MERCHANT_SPAWN_GRID_X < SCREEN_WIDTH // GRID_SIZE and \
                        0 <= ADV_MERCHANT_SPAWN_GRID_Y < SCREEN_HEIGHT // GRID_SIZE):
                    print(f"警告：高级商人预设生成位置 ({ADV_MERCHANT_SPAWN_GRID_X}, {ADV_MERCHANT_SPAWN_GRID_Y}) 超出地图边界。")
                    can_spawn = False
                
                if can_spawn:
                    # 检查目标位置是否有墙壁 (你可能需要一个更通用的检查方法)
                    for wall_like in self.walls: # 检查普通墙和关闭的门等
                        if wall_like.grid_x == ADV_MERCHANT_SPAWN_GRID_X and wall_like.grid_y == ADV_MERCHANT_SPAWN_GRID_Y:
                            print(f"警告：高级商人预设生成位置 ({ADV_MERCHANT_SPAWN_GRID_X}, {ADV_MERCHANT_SPAWN_GRID_Y}) 被墙壁阻挡。")
                            can_spawn = False
                            break
                
                if can_spawn:
                     # 检查地图原始布局字符，确保不是墙或其他固定物
                    if self.map_layout[ADV_MERCHANT_SPAWN_GRID_Y][ADV_MERCHANT_SPAWN_GRID_X] not in ['0', 'C', 'H', 'A']: # 允许在空地或原物品位置生成
                        print(f"警告：高级商人预设生成位置 ({ADV_MERCHANT_SPAWN_GRID_X}, {ADV_MERCHANT_SPAWN_GRID_Y}) 在地图上不是一个理想的空地 (当前字符: '{self.map_layout[ADV_MERCHANT_SPAWN_GRID_Y][ADV_MERCHANT_SPAWN_GRID_X]}')。")
                        # 你可以选择依然生成，或者不生成

                    adv_merchant = Merchant(self, ADV_MERCHANT_SPAWN_GRID_X, ADV_MERCHANT_SPAWN_GRID_Y,
                                            MERCHANT_ADVANCED_IMG_NAME, "advanced")
                    self.all_sprites.add(adv_merchant)
                    self.merchants_group.add(adv_merchant)
                    print("高级商人已生成！")
                else:
                    print("高级商人生成失败，请检查预设位置或地图。")
            # 目前我们只设置一个标志位。

    def run(self):
        while self.running:
            self.dt = self.clock.tick(FPS) / 1000.0 # Delta time in seconds
            self.events()
            self.update()
            self.draw()
        pygame.quit()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if self.current_game_state == STATE_MENU:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p: # P键调试，可以保留或移除
                        print("P1 Controls (MENU):", self.player1.control_keys)
                        print("P2 Controls (MENU):", self.player2.control_keys)
                    
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        print("Starting game from menu (ENTER pressed)...")
                        self.initialize_game_world()
                        self.current_game_state = STATE_PLAYING
                        pygame.display.set_caption("V.Klinge(Beta)")
            
            elif self.current_game_state == STATE_PLAYING:
                if event.type == pygame.KEYDOWN:
                    # --- P键调试 (确保在游戏内也能用) ---
                    if event.key == pygame.K_p:
                        print("--- IN-GAME P KEY PRESSED ---")
                        print("P1 Controls (IN-GAME):", self.player1.control_keys)
                        print("P2 Controls (IN-GAME):", self.player2.control_keys)
                    # ------------------------------------
                    
                    if event.key == pygame.K_ESCAPE:
                        print("Returning to menu...")
                        self.current_game_state = STATE_MENU
                        pygame.display.set_caption("V.Klinge(Beta)cover")
                    else:
                        # --- 玩家1 ---
                        if event.key == self.player1.control_keys['up']:
                            self.player1.move(dy=-1)
                        if event.key == self.player1.control_keys['down']:
                            self.player1.move(dy=1)
                        if event.key == self.player1.control_keys['left']:
                            self.player1.move(dx=-1)
                        if event.key == self.player1.control_keys['right']:
                            self.player1.move(dx=1)
                        if event.key == self.player1.control_keys['interact']:
                            self.player1.attempt_interaction()
                        if event.key == self.player1.control_keys['bomb']:
                            self.player1.place_bomb()

                        # --- 玩家2 ---
                        if event.key == self.player2.control_keys['up']:
                            self.player2.move(dy=-1)
                        if event.key == self.player2.control_keys['down']:
                            self.player2.move(dy=1)
                        if event.key == self.player2.control_keys['left']:
                            self.player2.move(dx=-1)
                        if event.key == self.player2.control_keys['right']:
                            self.player2.move(dx=1)
                        if event.key == self.player2.control_keys['interact']:
                            self.player2.attempt_interaction()
                        if event.key == self.player2.control_keys['bomb']:
                            self.player2.place_bomb()

            elif self.current_game_state == STATE_TRADING_NORMAL or \
                 self.current_game_state == STATE_TRADING_ADVANCED:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.current_game_state = STATE_PLAYING
                        self.current_interacting_merchant = None
                        self.current_interacting_player = None
                        print("退出交易界面。")
                    else: 
                        if self.current_game_state == STATE_TRADING_NORMAL:
                            if event.key == pygame.K_1: self.attempt_purchase_item(0)
                            elif event.key == pygame.K_2: self.attempt_purchase_item(1)
                        elif self.current_game_state == STATE_TRADING_ADVANCED:
                            if event.key == pygame.K_1: self.attempt_purchase_item(0)
                            elif event.key == pygame.K_2: self.attempt_purchase_item(1)
                            elif event.key == pygame.K_3: self.attempt_purchase_item(2)
                            elif event.key == pygame.K_4: self.attempt_purchase_item(3)
            elif self.current_game_state == STATE_GAME_WON: # <--- 新增对游戏胜利状态的事件处理
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False # 直接退出游戏
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        print("Returning to menu from game won screen...")
                        self.current_game_state = STATE_MENU # 返回主菜单
                        pygame.display.set_caption("V.Klinge(Beta)cover")
                        # initialize_game_world() 会在从菜单再次开始游戏时调用
            elif self.current_game_state == STATE_GAME_OVER: # <--- 新增对游戏失败状态的事件处理
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False # 直接退出游戏
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        print("Returning to menu from game over screen...")
                        self.current_game_state = STATE_MENU # 返回主菜单
                        pygame.display.set_caption("V.Klinge(Beta)cover")
                        # initialize_game_world() 会在从菜单再次开始游戏时调用

    def attempt_purchase_item(self, item_index):
        if not (self.current_interacting_merchant and self.current_interacting_player):
            print("不在交易状态或没有选中商人/玩家。")
            return

        wares_list = list(self.current_interacting_merchant.wares.items())
        player = self.current_interacting_player
        player_id_str = player_id_from_controls(player)

        if not (0 <= item_index < len(wares_list)):
            print("无效的商品选项。")
            return

        item_key_desc, item_details = wares_list[item_index]
        item_name_for_message = item_details['display_name']
        cost_value = item_details['cost']
        cost_type = item_details.get("cost_type", "gold") # 默认为金币支付

        if player.health <= 0 and cost_type != "health": # 如果死亡，且不是用生命支付（用生命支付时，允许在低血量尝试）
            print(f"玩家 {player_id_str} 已被击败，无法购买商品。")
            return

        # --- 检查购买条件 ---
        can_purchase = False
        if cost_type == "gold":
            if player.coins >= cost_value:
                can_purchase = True
            else:
                print(f"金币不足！购买 {item_name_for_message} 需要 {cost_value} 金币，玩家 {player_id_str} 只有 {player.coins}。")
        elif cost_type == "health":
            # 购买符箓至少需要比消耗的血量多1点生命，或者你可以设定一个最低生命值门槛
            if player.health > cost_value: # 例如，必须拥有大于消耗量的生命值
                can_purchase = True
            else:
                print(f"生命值不足！购买 {item_name_for_message} 需要消耗 {cost_value} 生命，玩家 {player_id_str} 只有 {player.health}。")
        
        if not can_purchase:
            return

        # --- 执行购买与扣费 ---
        if cost_type == "gold":
            player.coins -= cost_value
            print(f"Player {player_id_str} bought {item_name_for_message} for {cost_value} gold. Gold left: {player.coins}")
            # 普通商人消费统计
            if self.current_interacting_merchant.merchant_type == "normal":
                self.total_spent_at_merchant1 += cost_value # 注意这里是 cost_value
                # ... (生成开关的逻辑不变) ...
                if not self.merchant2_switch_spawned and self.total_spent_at_merchant1 >= MERCHANT1_SPEND_THRESHOLD_FOR_SWITCH:
                    self.spawn_switch_for_adv_merchant()

        elif cost_type == "health":
            player.health -= cost_value
            # 购买符箓后，血量不能为0或负数，如果上面检查 player.health > cost_value 则这里是安全的
            # 如果允许 player.health == cost_value 购买，则购买后血量会是0，需要处理死亡
            print(f"Player {player_id_str} spent {cost_value} HP for {item_name_for_message}. Current HP: {player.health}")


        # --- 应用物品效果 ---
        item_id = item_details['item_id']

        if item_id == "lifepotion" or item_id == "large_lifepotion": # 合并处理普通和强效生命药水
            heal_amount = item_details.get("heal_amount", 25) # large_lifepotion 会有自己的 heal_amount
            player.health += heal_amount
            # player.health = min(player.health + heal_amount, player.max_health) # <--- 移除对 max_health 的限制
            print(f"玩家 {player_id_str} 回复了 {heal_amount} 点生命，当前生命: {player.health}")

        elif item_id == "attackpotion":
            # ... (不变) ...
            attack_increase = item_details.get("attack_increase", 5)
            player.attack_power += attack_increase
            print(f"玩家 {player_id_str} 获得了攻击增幅！当前攻击力: {player.attack_power}")

        elif item_id == "perm_attack_boost":
            attack_increase = item_details.get("attack_increase", 2)
            player.attack_power += attack_increase
            print(f"玩家 {player_id_str} 永久提升了攻击力 {attack_increase}！当前攻击力: {player.attack_power}")

        elif item_id == "bomb_capacity":
            if not hasattr(player, 'max_bombs'): player.max_bombs = INITIAL_BOMBS
            player.max_bombs += 1
            player.bombs +=1
            print(f"玩家 {player_id_str} 提升了炸弹携带上限！当前上限: {player.max_bombs}, 当前炸弹数: {player.bombs}")

        elif item_id == "random_talisman":
            # 随机选择一个符箓效果
            possible_effects = ["crit_chance", "crit_damage", "dodge_chance"]
            chosen_effect = random.choice(possible_effects)
            
            talisman_applied_msg = f"玩家 {player_id_str} 获得的符箓增强了 "
            if chosen_effect == "crit_chance":
                increase = round(random.uniform(TALISMAN_CRIT_CHANCE_INCREASE_MIN, TALISMAN_CRIT_CHANCE_INCREASE_MAX), 3)
                player.crit_chance += increase
                player.crit_chance = min(player.crit_chance, 1.0) # 暴击率不超过100%
                talisman_applied_msg += f"暴击率 {increase*100:.1f}%！当前暴击率: {player.crit_chance*100:.1f}%"
            elif chosen_effect == "crit_damage":
                increase = round(random.uniform(TALISMAN_CRIT_DAMAGE_INCREASE_MIN, TALISMAN_CRIT_DAMAGE_INCREASE_MAX), 2)
                player.crit_damage_multiplier += increase
                talisman_applied_msg += f"暴击伤害倍率 {increase*100:.0f}%！当前暴击伤害: {player.crit_damage_multiplier*100:.0f}%"
            elif chosen_effect == "dodge_chance":
                increase = round(random.uniform(TALISMAN_DODGE_CHANCE_INCREASE_MIN, TALISMAN_DODGE_CHANCE_INCREASE_MAX), 3)
                player.dodge_chance += increase
                player.dodge_chance = min(player.dodge_chance, 0.9) # 闪避率不超过90% (或其他上限)
                talisman_applied_msg += f"闪避率 {increase*100:.1f}%！当前闪避率: {player.dodge_chance*100:.1f}%"
            print(talisman_applied_msg)
            
        else:
            print(f"未知的物品ID: {item_id} (效果未实现)")
                


    def update(self):
          if self.current_game_state == STATE_PLAYING:
            self.all_sprites.update() # 只在游戏进行时更新所有精灵
        # 在交易状态下，游戏世界的精灵通常不更新 (暂停)

    def draw_checkered_background(self, surface):
        """绘制黑白交错的格子背景"""
        for r in range(0, SCREEN_HEIGHT // GRID_SIZE):
            for c in range(0, SCREEN_WIDTH // GRID_SIZE):
                rect = pygame.Rect(c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                if (r + c) % 2 == 0:
                    pygame.draw.rect(surface, WHITE, rect) # 或者用 settings.WHITE
                else:
                    pygame.draw.rect(surface, LIGHT_GREY, rect) # 用 settings.GREY 或 LIGHT_GREY

    def draw_grid_lines(self, surface):
        """(可选) 绘制网格线，方便调试"""
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            pygame.draw.line(surface, DARK_GREY, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
            pygame.draw.line(surface, DARK_GREY, (0, y), (SCREEN_WIDTH, y))

    def draw_hud(self):
        # 定义用于 HUD 的字体，如果 small_font 未在 __init__ 中定义，则在此处定义
        # 或者确保 self.small_font 在 __init__ 中已正确初始化
        if not hasattr(self, 'small_font'): # 避免重复创建
            self.small_font = pygame.font.SysFont(None, 24) # 或者 "arial", 24

        # --- 玩家1 HUD (在屏幕左上角，单行) ---
        p1_text = (f"P1 HP: {self.player1.health} C: {self.player1.coins} ATK: {self.player1.attack_power} B: {self.player1.bombs} | "
                   f"Crit: {self.player1.crit_chance*100:.0f}% CD:x{self.player1.crit_damage_multiplier:.1f} Dodge: {self.player1.dodge_chance*100:.0f}%")
        p1_surf = self.small_font.render(p1_text, True, WHITE) # 使用 small_font
        p1_rect = p1_surf.get_rect(topleft=(10, 10))
        self.screen.blit(p1_surf, p1_rect)

        # --- 玩家2 HUD (在屏幕最下方，单行) ---
        p2_text = (f"P2 HP: {self.player2.health} C: {self.player2.coins} ATK: {self.player2.attack_power} B: {self.player2.bombs} | "
                   f"Crit: {self.player2.crit_chance*100:.0f}% CD:x{self.player2.crit_damage_multiplier:.1f} Dodge: {self.player2.dodge_chance*100:.0f}%")
        p2_surf = self.small_font.render(p2_text, True, WHITE) # 使用 small_font
        # 定位 P2 文本的矩形，使其底部在屏幕底部减去一些边距，并且左对齐
        p2_rect = p2_surf.get_rect(bottomleft=(10, SCREEN_HEIGHT - 10))
        self.screen.blit(p2_surf, p2_rect)

        # --- (可选) 显示高级商人解锁状态 ---
        # 这个提示现在需要考虑 P1 和 P2 HUD 的位置
        if self.adv_merchant_unlocked:
            unlock_text = "Advanced Merchant Unlocked!"
            # 使用 self.font (大小30) 或 self.small_font (大小24) 来渲染这个提示
            unlock_surf = self.font.render(unlock_text, True, (0, 255, 0)) # 绿色
            
            # 尝试将提示放在 P1 HUD 的下方，且在屏幕中央附近
            # 但也要确保它不会与可能在底部的 P2 HUD 重叠（如果 P1 HUD 很短）
            # 一个简单的做法是固定在屏幕的一个特定垂直位置，比如屏幕高度的1/4或1/5处
            #unlock_rect = unlock_surf.get_rect(centerx=SCREEN_WIDTH // 2, top=p1_rect.bottom + 15) # P1下方15像素

            # 或者，如果想让它更靠近底部但不与 P2 重叠：
            unlock_rect = unlock_surf.get_rect(centerx=SCREEN_WIDTH // 2, bottom=p2_rect.top - 15) # P2上方15像素

            self.screen.blit(unlock_surf, unlock_rect)

    def draw_trading_ui_normal(self):
        """绘制普通商人的交易界面"""
        if not self.current_interacting_merchant:
            return

        # 绘制一个半透明的背景遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) # 黑色，180的alpha透明度
        self.screen.blit(overlay, (0, 0))

        # 交易窗口的尺寸和位置
        win_width = SCREEN_WIDTH * 0.6
        win_height = SCREEN_HEIGHT * 0.7
        win_x = (SCREEN_WIDTH - win_width) / 2
        win_y = (SCREEN_HEIGHT - win_height) / 2
        trade_window_rect = pygame.Rect(win_x, win_y, win_width, win_height)
        pygame.draw.rect(self.screen, DARK_GREY, trade_window_rect) # 窗口背景
        pygame.draw.rect(self.screen, WHITE, trade_window_rect, 3)    # 窗口边框

        # 标题
        title_text = "Normal Shop (Press number to select, ESC to exit)"
        title_surf = self.large_font.render(title_text, True, WHITE)
        title_rect = title_surf.get_rect(centerx=trade_window_rect.centerx, top=trade_window_rect.top + 20)
        self.screen.blit(title_surf, title_rect)

        # 显示商品列表
        start_y = title_rect.bottom + 30
        item_index = 0
        # 我们用一个列表来保证顺序和数字选择的一致性
        displayable_wares = list(self.current_interacting_merchant.wares.items())

        for i, (key_desc, details) in enumerate(displayable_wares):
            # item_display_text = f"{i + 1}. {details['display_name']} - {details['cost']} Gold"
            item_display_text = key_desc # 直接使用键名，它现在是英文描述
            item_surf = self.font.render(item_display_text, True, WHITE)
            item_rect = item_surf.get_rect(left=trade_window_rect.left + 30, top=start_y + i * 40)
            self.screen.blit(item_surf, item_rect)

        if self.current_interacting_player:
            # 玩家金币显示改为英文
            player_coins_text = f"Your Gold: {self.current_interacting_player.coins} HP: {self.current_interacting_player.health}" # 也显示HP
            player_coins_surf = self.font.render(player_coins_text, True, YELLOW if hasattr(pygame.colordict, 'YELLOW') else WHITE)
            player_coins_rect = player_coins_surf.get_rect(left=trade_window_rect.left + 30, bottom=trade_window_rect.bottom - 20)
            self.screen.blit(player_coins_surf, player_coins_rect)

    def draw_trading_ui_advanced(self):
        if not self.current_interacting_merchant:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        win_width = SCREEN_WIDTH * 0.75 # 可以微调窗口大小
        win_height = SCREEN_HEIGHT * 0.85
        win_x = (SCREEN_WIDTH - win_width) / 2
        win_y = (SCREEN_HEIGHT - win_height) / 2
        trade_window_rect = pygame.Rect(win_x, win_y, win_width, win_height)
        pygame.draw.rect(self.screen, (30, 30, 70), trade_window_rect)
        pygame.draw.rect(self.screen, YELLOW, trade_window_rect, 3)

        title_text = "Mystic Emporium (Press number, ESC to exit)" # 换个酷炫点的名字
        title_surf = self.large_font.render(title_text, True, YELLOW)
        title_rect = title_surf.get_rect(centerx=trade_window_rect.centerx, top=trade_window_rect.top + 20)
        self.screen.blit(title_surf, title_rect)

        start_y = title_rect.bottom + 30 # 调整商品列表起始位置
        item_spacing = 40 # 商品间距
        current_item_y = start_y # 使用一个变量来跟踪当前绘制项的Y坐标，以应对提示文字

        displayable_wares = list(self.current_interacting_merchant.wares.items())

        for i, (key_desc, details) in enumerate(displayable_wares):
            item_display_text = key_desc # 这个 key_desc 已经包含了价格和货币类型
            
            # 根据 cost_type 改变文字颜色，可选
            text_color = WHITE
            if details.get("cost_type") == "health":
                text_color = (255, 100, 100) # 淡红色表示消耗生命

            item_surf = self.font.render(item_display_text, True, text_color)
            #item_rect = item_surf.get_rect(left=trade_window_rect.left + 30, top=start_y + i * item_spacing)
            item_rect = item_surf.get_rect(left=trade_window_rect.left + 30, top=current_item_y)
            self.screen.blit(item_surf, item_rect)
            current_item_y += item_surf.get_height() + 5 # 更新Y坐标，加上一点小间隙

            # 如果是随机符箓，可以加一行小字提示
            if details['item_id'] == "random_talisman":
                talisman_hint_text = "(Randomly boosts Crit Chance, Crit Damage, or Dodge Chance)"
                hint_font = pygame.font.SysFont(None, 22) # 更小的字体
                hint_surf = hint_font.render(talisman_hint_text, True, GREY) # 灰色提示
                hint_rect = hint_surf.get_rect(left=item_rect.left + 15, top=item_rect.bottom + 1)
                self.screen.blit(hint_surf, hint_rect)
                #start_y += 15 # 为提示文字额外增加一点垂直空间
                current_item_y += hint_surf.get_height() + 10 # 为提示文字额外增加垂直空间并加上额外间隙

        # 显示玩家信息，包括新属性
        if self.current_interacting_player:
            p = self.current_interacting_player
            player_stats_lines = [
                f"Gold: {p.coins}",
                f"HP: {p.health} Bombs: {p.bombs}/{p.max_bombs}",
                f"Attack: {p.attack_power}",
                f"Crit Chance: {p.crit_chance*100:.1f}%",
                f"Crit Damage: x{p.crit_damage_multiplier:.2f}",
                f"Dodge Chance: {p.dodge_chance*100:.1f}%"
            ]
            
            player_info_start_y = trade_window_rect.bottom - 20 - (len(player_stats_lines) * 22) # 从底部向上排列

            for i, line in enumerate(player_stats_lines):
                line_surf = self.font.render(line, True, YELLOW)
                line_rect = line_surf.get_rect(left=trade_window_rect.left + 30, top=player_info_start_y + i * 22)
                self.screen.blit(line_surf, line_rect)

    def draw(self):
        #self.screen.fill(BLACK) # 先用纯色填充
       # self.draw_checkered_background(self.screen)
        # self.draw_grid_lines(self.screen) # 如果需要，取消注释

        # 根据游戏状态绘制不同的内容
        if self.current_game_state == STATE_MENU: # <--- 新增分支
            self.draw_menu()
        elif self.current_game_state == STATE_PLAYING:
            self.screen.fill(BLACK) # 为游戏区域填充背景色
            self.draw_checkered_background(self.screen)
            self.all_sprites.draw(self.screen)
            self.draw_hud()
        elif self.current_game_state == STATE_TRADING_NORMAL:
            self.screen.fill(BLACK) # 为游戏区域填充背景色
            self.draw_checkered_background(self.screen)
            self.all_sprites.draw(self.screen)
            self.draw_hud()
            self.draw_trading_ui_normal()
        elif self.current_game_state == STATE_TRADING_ADVANCED:
            self.screen.fill(BLACK) # 为游戏区域填充背景色
            self.draw_checkered_background(self.screen)
            self.all_sprites.draw(self.screen)      # 绘制游戏世界作为背景
            self.draw_hud()                         # 绘制 HUD
            self.draw_trading_ui_advanced()         # 绘制高级商人交易界面
        elif self.current_game_state == STATE_GAME_WON: # <--- 新增分支
            self.draw_game_won_screen()
        elif self.current_game_state == STATE_GAME_OVER: # <--- 新增分支
            self.draw_game_over_screen()
            
        pygame.display.flip()

# 辅助函数，用于从玩家控制配置中获取ID（用于打印）
def player_id_from_controls(player_sprite):
    if player_sprite.control_keys['up'] == pygame.K_w:
        return "P1"
    elif player_sprite.control_keys['up'] == pygame.K_UP:
        return "P2"
    return "UnknownPlayer"        
# --- 游戏主程序入口 ---
if __name__ == '__main__':
   
    game = Game()
    game.run()
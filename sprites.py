_author_='WenAlis'
# sprites.py
import pygame
import random # 用于震动效果
from settings import * # 导入所有设置

class Player(pygame.sprite.Sprite):
    def __init__(self, game, grid_x, grid_y, image_filename, control_keys):
        super().__init__() # 或者 pygame.sprite.Sprite.__init__(self)
        self.game = game # 引用主游戏对象，方便访问其他游戏组件
        self.image_original = load_image(image_filename, scale_to_grid=True)
        self.image = self.image_original.copy()
        self.rect = self.image.get_rect()
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.rect.topleft = (self.grid_x * GRID_SIZE, self.grid_y * GRID_SIZE)

        # 存储控制按键方案
        self.control_keys = control_keys # 例如 {'up': pygame.K_w, 'down': pygame.K_s, ...}

        # 玩家属性 (以后可以扩展)
        self.initial_health = 100
        self.health = self.initial_health
        self.is_dead = False # 新增一个明确的死亡标记，虽然 health <= 0 也能判断
        
        self.coins = 0
        # 初始攻击力
        self.initial_attack_power = 10 # 或者从 settings.py 读取 PLAYER_INITIAL_ATTACK_POWER
        self.attack_power = self.initial_attack_power

        # 初始炸弹数量和上限
        self.initial_bombs = INITIAL_BOMBS # 来自 settings.py
        self.bombs = self.initial_bombs
        self.initial_max_bombs = 10 # 你在代码中设定的初始上限，或者也可以来自 settings
        self.max_bombs = self.initial_max_bombs

        # --- 新增：符箓相关属性 ---
        self.initial_crit_chance = 0.3  # 初始暴击率 (例如 30%)
        self.crit_chance = self.initial_crit_chance
        self.initial_crit_damage_multiplier = 1.5 # 这是暴击时的伤害倍数
        self.crit_damage_multiplier = self.initial_crit_damage_multiplier
        self.initial_dodge_chance = 0.0  # 闪避通常从0开始
        self.dodge_chance = self.initial_dodge_chance

        # 玩家抖动相关属性
        self.is_shaking = False
        self.shake_end_time = 0
        # self.original_pos_for_shake = self.rect.topleft # 在start_shaking中设置
        # ... 其他属性
    def reset_state(self, start_grid_x=None, start_grid_y=None):
        """重置玩家到初始状态和位置"""
        self.grid_x = start_grid_x if start_grid_x is not None else self.initial_grid_x
        self.grid_y = start_grid_y if start_grid_y is not None else self.initial_grid_y
        self.rect.topleft = (self.grid_x * GRID_SIZE, self.grid_y * GRID_SIZE)

        self.health = self.initial_health 
        # if hasattr(self, 'max_health'): self.max_health = 100 # 重置最大生命
        self.coins = 0
        self.attack_power = self.initial_attack_power # 重置为基础攻击力
        self.bombs = self.initial_bombs
        # 确保 max_bombs 也被重置为其初始上限
        if hasattr(self, 'initial_max_bombs'): # 检查是否存在
            self.max_bombs = self.initial_max_bombs
        else: # 如果没有 initial_max_bombs，则根据你的设计来设置，例如回到一个固定的初始上限
            self.max_bombs = 10 # 或者从 settings.py 读取一个初始的炸弹上限常量

        self.crit_chance = self.initial_crit_chance
        self.crit_damage_multiplier = self.initial_crit_damage_multiplier
        self.dodge_chance = self.initial_dodge_chance
        
        self.is_shaking = False # 确保不处于抖动状态
        print(f"Player reset to stats and position ({self.grid_x}, {self.grid_y})")
        self.is_dead = False # 重置死亡标记

    def move(self, dx=0, dy=0):
        """根据格子偏移量移动玩家"""
        # 如果玩家正在抖动，或者已死亡，则不允许移动 (简单处理)
        if self.is_shaking or self.health <= 0: # 新增：死亡或抖动时不能移动
            return
        new_grid_x = self.grid_x + dx
        new_grid_y = self.grid_y + dy

        # 边界检查 (基于屏幕格子数)
        # 注意：这里我们还没有墙壁碰撞，所以可以自由移动
        max_grid_x = SCREEN_WIDTH // GRID_SIZE - 1
        max_grid_y = SCREEN_HEIGHT // GRID_SIZE - 1

        if 0 <= new_grid_x <= max_grid_x and 0 <= new_grid_y <= max_grid_y:
            # 在这里我们会加入墙壁碰撞检测
            if not self.check_wall_collision(new_grid_x, new_grid_y):
                # 2. 检查是否撞到怪物
                collided_monster = self.check_monster_collision(new_grid_x, new_grid_y)
                if collided_monster:
                    # 如果撞到怪物，攻击怪物，玩家不移动到怪物格子上
                    self.attack_monster(collided_monster)
                else:
                    # 如果没撞到怪物，移动到新位置
                    self.grid_x = new_grid_x
                    self.grid_y = new_grid_y
                    # 更新玩家精灵的屏幕像素位置
                    self.rect.topleft = (self.grid_x * GRID_SIZE, self.grid_y * GRID_SIZE)
                    # 在成功移动到新位置后，检查是否踩到了物品
                    self.check_item_collision()
                # 如果目标位置超出边界，或者撞墙了，则玩家不移动，grid_x, grid_y 和 rect 都不更新
                # 也不需要检查物品碰撞，因为玩家没有移动到新格子

        

    def check_wall_collision(self, next_grid_x, next_grid_y):
        """检查目标格子是否有墙壁"""
        # 我们需要访问地图数据，所以game对象需要有地图信息
        if hasattr(self.game, 'walls'): # 确保game对象有walls组
            for wall in self.game.walls:
                if wall.grid_x == next_grid_x and wall.grid_y == next_grid_y:
                    print(f"Player trying to move to wall at ({next_grid_x}, {next_grid_y})") # 调试信息
                    return True # 发生碰撞
        return False # 没有碰撞
    def check_monster_collision(self, next_grid_x, next_grid_y):
        """检查目标格子是否有怪物"""
        if hasattr(self.game, 'monsters_group'):
            for monster in self.game.monsters_group:
                # 确保怪物还活着才进行碰撞和攻击
                if monster.health > 0 and monster.grid_x == next_grid_x and monster.grid_y == next_grid_y:
                    return monster
        return None # 没有碰撞到怪物

    def attack_monster(self, monster):
        """攻击怪物，并传递自身作为攻击者"""
        player_id = "P1" if self.control_keys['up'] == pygame.K_w else "P2"
        print(f"玩家 {player_id} 攻击了在 ({monster.grid_x}, {monster.grid_y}) 的怪物!")
        monster.take_damage(self.attack_power, self) # 传递 self (当前玩家对象)

  
    def check_item_collision(self):
        """检查玩家是否与物品碰撞 (金币或药水)"""
        player_id = "P1" if self.control_keys['up'] == pygame.K_w else "P2"

        # 检查金币
        collided_coins = pygame.sprite.spritecollide(self, self.game.coins_group, True)
        for coin in collided_coins:
            self.coins += coin.value
            print(f"玩家 {player_id} 拾取了价值 {coin.value} 的金币！总金币: {self.coins}")

        # 检查药水 (假设药水在 self.game.potions_group 中)
        if hasattr(self.game, 'potions_group'):
            collided_potions = pygame.sprite.spritecollide(self, self.game.potions_group, False) # dokill=False，让Potion自己处理kill
            for potion in collided_potions:
                potion.apply_effect(self) # 调用药水自己的 apply_effect 方法
                                          # apply_effect 内部会调用 potion.kill()
        # --- 新增：检查符箓拾取物 ---
        if hasattr(self.game, 'talisman_pickups_group'):
            # dokill=False 因为 TalismanPickup 的 apply_random_talisman_effect 方法会自己调用 self.kill()
            collided_talismans = pygame.sprite.spritecollide(self, self.game.talisman_pickups_group, False)
            for talisman in collided_talismans:
                talisman.apply_random_talisman_effect(self) # 调用符箓自己的效果应用方法
    def attempt_interaction(self):
        """尝试与相邻格子的NPC或可互动对象（如开关、传送门）互动"""
        if self.health <= 0: return False

        # 玩家当前站立的格子也可以是传送门的目标
        # 或者只检查相邻格子，取决于你的设计
        interaction_check_coords = [
            (self.grid_x, self.grid_y), # 检查当前站立的格子 (如果门消失了，玩家可以站在门的位置)
            (self.grid_x, self.grid_y - 1),
            (self.grid_x, self.grid_y + 1),
            (self.grid_x - 1, self.grid_y),
            (self.grid_x + 1, self.grid_y)
        ]

        # 检查传送门
        if hasattr(self.game, 'doors_group'):
            for door in self.game.doors_group:
                if door.is_portal and door.is_open: # 只与打开的传送门互动
                    if door.grid_x == self.grid_x and door.grid_y == self.grid_y:
                        print(f"DEBUG: Player is ON the portal at ({door.grid_x},{door.grid_y}). Calling door.interact().") # 添加调试
                        if door.interact(self):
                            return True
                         # 如果是检查相邻，则用之前的 possible_interaction_coords 逻辑
                         # else:
                         #     possible_interaction_coords_for_door = [
                         #         (self.grid_x, self.grid_y - 1), (self.grid_x, self.grid_y + 1),
                         #         (self.grid_x - 1, self.grid_y), (self.grid_x + 1, self.grid_y)
                         #     ]
                         #     if (door.grid_x, door.grid_y) in possible_interaction_coords_for_door:
                         #        if door.interact(self): return True


        # 检查开关
        if hasattr(self.game, 'switches_group'):
            for switch in self.game.switches_group:
                # 开关通常在旁边按，而不是站在上面按
                possible_interaction_coords_for_switch = [
                    (self.grid_x, self.grid_y - 1), (self.grid_x, self.grid_y + 1),
                    (self.grid_x - 1, self.grid_y), (self.grid_x + 1, self.grid_y)
                ]
                if (switch.grid_x, switch.grid_y) in possible_interaction_coords_for_switch:
                    if switch.interact(self):
                        return True

        # 检查商人
        if hasattr(self.game, 'merchants_group'):
            for merchant in self.game.merchants_group:
                 possible_interaction_coords_for_merchant = [
                    (self.grid_x, self.grid_y - 1), (self.grid_x, self.grid_y + 1),
                    (self.grid_x - 1, self.grid_y), (self.grid_x + 1, self.grid_y)
                ]
                 if (merchant.grid_x, merchant.grid_y) in possible_interaction_coords_for_merchant:
                    merchant.interact(self)
                    return True

        print("Player tried to interact, but no interactable object found nearby or conditions not met.")
        return False


    # --- 新增：玩家受伤害和抖动逻辑 ---
    def take_damage(self, amount):
        if self.health <= 0: # 如果已经死亡，不再承受伤害
            return

        self.health -= amount
        player_id = "P1" if self.control_keys['up'] == pygame.K_w else "P2"
        print(f"玩家 {player_id} 受到 {amount} 点伤害，剩余生命: {self.health}")
        if self.health > 0: # 如果受伤但未死亡
            self.start_shaking()
            return # 直接返回，不执行后续死亡判断

        # --- 玩家死亡逻辑 ---
        self.health = 0
        self.is_dead = True # 标记为死亡
        print(f"玩家 {player_id} 被击败了！")

        # 检查是否在BOSS战中 (Game对象需要一个标志位 is_boss_active)
        # 并且 self.game.boss_entity 存在且存活
        is_boss_battle_active = hasattr(self.game, 'is_boss_active') and self.game.is_boss_active and \
                                self.game.boss_entity and self.game.boss_entity.alive()

        if is_boss_battle_active:
            print(f"DEBUG: Player {player_id} died during active boss battle.")
            # 确定另一个玩家是谁
            other_player = None
            if self == self.game.player1:
                other_player = self.game.player2
            elif self == self.game.player2:
                other_player = self.game.player1

            if other_player and other_player.health > 0: # 如果另一个玩家还活着
                print(f"玩家 {player_id} 阵亡！另一个玩家 ({'P2' if other_player == self.game.player2 else 'P1'}) 获得绝境爆发！")
                other_player.health += SURVIVOR_BONUS_HEALTH
                other_player.attack_power += SURVIVOR_BONUS_ATTACK
                other_player.dodge_chance += SURVIVOR_BONUS_DODGE
                other_player.crit_chance += SURVIVOR_BONUS_CRIT
                # 确保属性不超过上限
                other_player.dodge_chance = min(other_player.dodge_chance, 0.9) # 例如闪避上限90%
                other_player.crit_chance = min(other_player.crit_chance, 1.0)   # 暴击上限100%
                
                print(f"幸存玩家新属性 - HP: {other_player.health}, ATK: {other_player.attack_power}, Dodge: {other_player.dodge_chance*100:.0f}%, Crit: {other_player.crit_chance*100:.0f}%")
                # 此处死亡的玩家的逻辑结束，另一个玩家获得了buff
            else: # 另一个玩家也死了，或者不存在 (单人模式下，不过你的是双人)
                print("所有玩家均已阵亡或另一玩家已死亡！触发游戏结束。")
                if self.game.current_game_state != STATE_GAME_OVER and self.game.current_game_state != STATE_GAME_WON:
                    self.game.trigger_game_over("Both heroes have fallen before the mighty foe...") # 传递一个失败原因
        else: # 非BOSS战期间死亡
            # 检查是否所有玩家都死亡了
            if self.game.player1.health <= 0 and self.game.player2.health <= 0:
                 if self.game.current_game_state != STATE_GAME_OVER and self.game.current_game_state != STATE_GAME_WON:
                    self.game.trigger_game_over("Defeated. Try again, heroes.。")
        
    def start_shaking(self):
        if not self.is_shaking:
            self.is_shaking = True
            self.shake_end_time = pygame.time.get_ticks() + PLAYER_SHAKE_DURATION
            self.original_pos_for_shake = self.rect.topleft # 记录当前位置作为抖动基准

    def place_bomb(self):
        """玩家尝试在当前位置放置炸弹"""
        if self.health <=0: return # 死亡不能放炸弹

        if self.bombs > 0:
            # 检查当前格子是否已经有炸弹 (简单检查，避免重叠放置太多)
            for bomb_sprite in self.game.bombs_group:
                if bomb_sprite.grid_x == self.grid_x and bomb_sprite.grid_y == self.grid_y:
                    print("这里已经有一个炸弹了！")
                    return

            print(f"玩家在 ({self.grid_x}, {self.grid_y}) 放置了一个炸弹。")
            bomb = Bomb(self.game, self.grid_x, self.grid_y, self) # 传递放置者
            self.game.all_sprites.add(bomb)
            self.game.bombs_group.add(bomb)
            self.bombs -= 1
        else:
            print("没有炸弹了！")
    def update(self):
        # 如果玩家死亡，也可以在这里处理一些持续效果，比如逐渐透明等
        if self.health <= 0:
            # 示例：死亡后图片可以做一些变化，比如半透明
            # self.image.set_alpha(128) # 但要注意convert_alpha()对set_alpha的影响
            return # 死亡后不进行抖动等更新

        if self.is_shaking:
            current_time = pygame.time.get_ticks()
            if current_time < self.shake_end_time:
                offset_x = random.randint(-PLAYER_SHAKE_INTENSITY, PLAYER_SHAKE_INTENSITY)
                offset_y = random.randint(-PLAYER_SHAKE_INTENSITY, PLAYER_SHAKE_INTENSITY)
                # 抖动是基于original_pos_for_shake，而不是当前可能因移动改变的self.rect.topleft
                self.rect.topleft = (self.original_pos_for_shake[0] + offset_x,
                                     self.original_pos_for_shake[1] + offset_y)
            else:
                self.is_shaking = False
                # 抖动结束后，确保玩家图像回到其逻辑格子的正确位置
                self.rect.topleft = (self.grid_x * GRID_SIZE, self.grid_y * GRID_SIZE)
        else:
            # 不抖动时，也确保位置正确（通常由move方法保证，但这里作为双重保险）
            # 如果玩家在此帧没有移动，rect.topleft保持不变即可。
            # 如果抖动刚结束，上面已经设置回去了。
            # 为避免冲突，只有在不抖动且不由move方法更新时，这里才需要强制校准。
            # 目前的结构，move方法会处理移动后的rect.topleft，所以这里可以简化。
            # 关键是抖动结束后要正确恢复到基于grid的位置。
             self.rect.topleft = (self.grid_x * GRID_SIZE, self.grid_y * GRID_SIZE)


    def draw(self, surface):
        """将玩家绘制到指定的surface上"""
        surface.blit(self.image, self.rect)

class Wall(pygame.sprite.Sprite):
    def __init__(self, game, grid_x, grid_y):
        super().__init__()
        self.game = game
        self.image = load_image(TILE_WALL_IMG_NAME, scale_to_grid=True)
        self.rect = self.image.get_rect()
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.rect.topleft = (self.grid_x * GRID_SIZE, self.grid_y * GRID_SIZE)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

class Coin(pygame.sprite.Sprite):
    def __init__(self, game, grid_x, grid_y):
        super().__init__()
        self.game = game
        # 金币图片可以不强制缩放到整个格子大小，让它小一点可能更好看
        self.image = load_image(ITEM_COIN_IMG_NAME, scale_to_grid=False) # scale_to_grid=False
        # 如果想让金币也严格64x64，就设为True，或者在load_image后手动调整
        # self.image = pygame.transform.scale(self.image, (GRID_SIZE // 2, GRID_SIZE // 2)) # 例如缩放到半个格子大小

        self.rect = self.image.get_rect()
        self.grid_x = grid_x
        self.grid_y = grid_y
        # 将金币的中心点定位在对应格子的中心点
        self.rect.centerx = self.grid_x * GRID_SIZE + GRID_SIZE // 2
        self.rect.centery = self.grid_y * GRID_SIZE + GRID_SIZE // 2
        self.value = 1 # 每个金币的价值，可以根据需要调整或随机化

    def draw(self, surface): # 虽然Sprite.Group会自动调用draw，但保留它也没问题
        surface.blit(self.image, self.rect)
# 怪物类
class Monster(pygame.sprite.Sprite):
    def __init__(self, game, grid_x, grid_y, image_filename,spawned_by_switch=None):
        super().__init__()
        self.game = game
        self.image_original = load_image(image_filename, scale_to_grid=True)
        self.image = self.image_original.copy()
        self.rect = self.image.get_rect()
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.rect.topleft = (self.grid_x * GRID_SIZE, self.grid_y * GRID_SIZE)

        self.health = MONSTER_HEALTH # 从settings中获取怪物血量
        self.attack_power = MONSTER_ATTACK_POWER
        self.is_shaking = False
        self.shake_timer = 0
        self.shake_end_time = 0
        self.original_pos_for_shake = self.rect.topleft  # 记录原始位置用于震动恢复
        self.gold_value = MONSTER_GOLD_DROP # 怪物携带的金币数量
        self.spawned_by_switch = spawned_by_switch # 记录生成此怪物的开关对象

    def take_damage(self, amount, attacker=None):
        # ... (之前的伤害计算和打印逻辑不变) ...
        if self.health <= 0: return
        self.health -= amount
        # ... (attacker_description 和 responsible_player_for_gold 逻辑不变) ...
        attacker_description = "Unknown attacker"; responsible_player_for_gold = None
        if isinstance(attacker, Player):
            attacker_description = "P1" if attacker.control_keys['up'] == pygame.K_w else "P2"
            responsible_player_for_gold = attacker
        elif isinstance(attacker, Bomb):
            attacker_description = "Bomb"
            if hasattr(attacker, 'placer') and isinstance(attacker.placer, Player):
                responsible_player_for_gold = attacker.placer
                placer_id = "P1" if attacker.placer.control_keys['up'] == pygame.K_w else "P2"
                attacker_description = f"Bomb (placed by {placer_id})"
        print(f"怪物在 ({self.grid_x}, {self.grid_y}) 受到来自 {attacker_description} 的 {amount} 点伤害，剩余血量: {self.health}")


        if self.health <= 0:
            self.health = 0
            print(f"怪物在 ({self.grid_x}, {self.grid_y}) 被 {attacker_description} 击败！")

            if responsible_player_for_gold:
                responsible_player_for_gold.coins += self.gold_value
                player_id_for_gold_message = "P1" if responsible_player_for_gold.control_keys['up'] == pygame.K_w else "P2"
                print(f"玩家 {player_id_for_gold_message} 获得了 {self.gold_value} 金币。总金币: {responsible_player_for_gold.coins}")
            else:
                print(f"怪物被击败，但金币未授予给特定玩家 (攻击者类型: {type(attacker)})。")

            # --- 新增：通知关联的开关 ---
            if self.spawned_by_switch:
                self.spawned_by_switch.monster_defeated(self)

            self.kill()
        else:
            self.start_shaking()
            if isinstance(attacker, Player):
                self.attack_player(attacker)
    def attack_player(self, player_to_attack):
        if player_to_attack.health > 0 : # 只攻击活着的玩家
            print(f"怪物 ({self.grid_x},{self.grid_y}) 反击玩家!")
            player_to_attack.take_damage(self.attack_power)

    def start_shaking(self):
        """开始震动效果"""
        if not self.is_shaking:
            self.is_shaking = True
            self.shake_end_time = pygame.time.get_ticks() + MONSTER_SHAKE_DURATION
            self.original_pos_for_shake = self.rect.topleft # 确保记录的是当前位置

    def update(self):
        if self.health <= 0: # 死亡的怪物不更新
            return
        """每帧更新怪物状态，主要处理震动效果"""
        if self.is_shaking:
            current_time = pygame.time.get_ticks()
            if current_time < self.shake_end_time:
                offset_x = random.randint(-MONSTER_SHAKE_INTENSITY, MONSTER_SHAKE_INTENSITY)
                offset_y = random.randint(-MONSTER_SHAKE_INTENSITY, MONSTER_SHAKE_INTENSITY)
                # 使用 self.original_pos_for_shake 作为基准
                self.rect.topleft = (self.original_pos_for_shake[0] + offset_x,
                                     self.original_pos_for_shake[1] + offset_y)
            else:
                self.is_shaking = False
                # 恢复到基于 original_pos_for_shake 的位置，或者其逻辑格子位置
                # 更稳妥的是恢复到其逻辑格子的像素位置，以防 original_pos_for_shake 在抖动中被意外改变（虽然不太可能）
                self.rect.topleft = (self.grid_x * GRID_SIZE, self.grid_y * GRID_SIZE) # <--- 或者 self.original_pos_for_shake 如果你确信它没问题
        else:
            # 非抖动时，确保怪物位置与逻辑格子同步
            self.rect.topleft = (self.grid_x * GRID_SIZE, self.grid_y * GRID_SIZE)

    def draw(self, surface): # Sprite.Group 会自动调用，但保留也无妨
        surface.blit(self.image, self.rect)
# --- 新增 Button 和 Door 类 ---
class Button(pygame.sprite.Sprite):
    def __init__(self, game, grid_x, grid_y, pair_id):
        super().__init__()
        self.game = game
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.pair_id = pair_id

        # 加载两种状态的图片
        self.image_on = load_image(BUTTON_ON_IMG_NAME, scale_to_grid=True)
        self.image_off = load_image(BUTTON_OFF_IMG_NAME, scale_to_grid=True)

        self.image = self.image_off # 初始状态为 "off" (未激活)
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.grid_x * GRID_SIZE, self.grid_y * GRID_SIZE)
        self.is_pressed = False # 逻辑状态

    def update(self):
        """检查是否有玩家踩在按钮上，并更新逻辑状态"""
        was_pressed = self.is_pressed
        self.is_pressed = False

        # 检查任一玩家是否在按钮上
        if (self.game.player1.grid_x == self.grid_x and self.game.player1.grid_y == self.grid_y) or \
           (self.game.player2.grid_x == self.grid_x and self.game.player2.grid_y == self.grid_y):
            self.is_pressed = True
        # 根据是否被按下，切换按钮的图片
        if self.is_pressed:
            self.image = self.image_on
        else:
            self.image = self.image_off
            
        # 如果按钮的逻辑状态改变，通知对应的门
        if self.is_pressed != was_pressed:
            self.game.notify_door(self.pair_id, self.is_pressed)
            # print(f"Button {self.pair_id} at ({self.grid_x},{self.grid_y}) logic state: {self.is_pressed}")

class Door(pygame.sprite.Sprite):
    def __init__(self, game, grid_x, grid_y, pair_id,is_portal=False,is_final_portal_trigger=False):
        super().__init__()
        self.game = game
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.pair_id = pair_id
        self.is_portal = is_portal # 标记这扇门是否是传送门
        self.is_final_portal_trigger = is_final_portal_trigger # <--- 新增属性


        self.image_closed = load_image(DOOR_IMG_NAME, scale_to_grid=True) # 使用 settings 中的 DOOR_IMG_NAME
        self.image_transparent = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        # self.image_transparent.fill((0,0,0,0)) # 确保透明 (SRCALPHA默认就是透明的)

        self.image = self.image_closed # 初始为关闭并可见
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.grid_x * GRID_SIZE, self.grid_y * GRID_SIZE)
        self.is_open = False # 逻辑状态: True 表示无碰撞，视觉上“消失”
        self.is_wall_when_closed = True # 关闭时表现为墙

    def set_state(self, is_open_param):
        """根据按钮状态设置门的逻辑状态和视觉表现"""
        self.is_open = is_open_param
        if self.is_open: # 门“消失” (逻辑打开，无碰撞，视觉透明)
            if self.is_wall_when_closed and self in self.game.walls:
                self.game.walls.remove(self)
            self.image = self.image_transparent
            # print(f"Door {self.pair_id} at ({self.grid_x},{self.grid_y}) is now LOGICALLY OPEN (transparent, no collision).")
        else: # 门“出现” (逻辑关闭，有碰撞，视觉为门)
            self.image = self.image_closed
            if self.is_wall_when_closed and self not in self.game.walls:
                self.game.walls.add(self)
            # print(f"Door {self.pair_id} at ({self.grid_x},{self.grid_y}) is now LOGICALLY CLOSED (visible, has collision).")

    def interact(self, player):
        if self.is_open:
            if self.is_final_portal_trigger: # <--- 检查是否是最终传送门
                player_id = "P1" if player.control_keys['up'] == pygame.K_w else "P2"
                print(f"玩家 {player_id} 激活了通往最终BOSS的传送门 ({self.grid_x},{self.grid_y})！")
                self.game.spawn_final_boss() # <--- 调用Game类的方法生成BOSS
                self.kill() # 传送门使用后消失 (可选)
                return True # 交互成功
            elif self.is_portal: # 普通传送门
                player_id = "P1" if player.control_keys['up'] == pygame.K_w else "P2"
                print(f"玩家 {player_id} 在打开的传送门 ({self.grid_x},{self.grid_y}) 按下E！准备传送到下一区域...")
                self.game.trigger_level_transition()
                return True
        return False

    def update(self):
        pass
class Merchant(pygame.sprite.Sprite):
    def __init__(self, game, grid_x, grid_y, image_filename, merchant_type="normal"):
        super().__init__()
        self.game = game
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.image_original = load_image(image_filename, scale_to_grid=True)
        self.image = self.image_original.copy()
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.grid_x * GRID_SIZE, self.grid_y * GRID_SIZE)
        self.merchant_type = merchant_type # "normal", "advanced" 等

        # 商人出售的物品 (示例，以后会更复杂)
        if self.merchant_type == "normal":
            self.wares = {
                # 将中文键名和描述改为英文
                "1. Health Potion (5 Gold)": {"item_id": "lifepotion", "cost": 5, "effect": "heal_player", "display_name": "Health Potion"},
                "2. Attack Buff (10 Gold)": {"item_id": "attackpotion", "cost": 10, "effect": "buff_attack", "display_name": "Attack Buff"}
            }
        elif self.merchant_type == "advanced":
            self.wares = {
                "1. Potent Healing Draught (+75 HP) (25 Gold)": {"item_id": "large_lifepotion", "cost": 25, "display_name": "Potent Healing", "heal_amount": 75, "cost_type": "gold"},

                "2. Permanent Attack Boost (+8) (50 Gold)": {"item_id": "perm_attack_boost", "cost": 50, "display_name": "Perm. Attack Up", "attack_increase": 8, "cost_type": "gold"},
                "3. Extra Bomb Capacity (+1) (30 Gold)": {"item_id": "bomb_capacity", "cost": 30, "display_name": "Bomb Capacity +1", "cost_type": "gold"}, # 假设炸弹上限仍需要

                f"4. Gamble for a Random Talisman ({TALISMAN_HEALTH_COST} Current HP)": { # 修改描述，明确是当前HP
                    "item_id": "random_talisman",
                    "cost": TALISMAN_HEALTH_COST,
                    "display_name": "Random Talisman",
                    "cost_type": "health"
                }
            }
        # ... (interact 方法之前已经修改过来支持 STATE_TRADING_ADVANCED) ...

    def update(self):
        # 商人通常是静态的，除非有动画
        pass

    def interact(self, player): # 确保这个方法是更新过的
        """玩家与商人互动"""
        print(f"玩家与 {self.merchant_type} 商人 ({self.grid_x},{self.grid_y}) 互动。")
        interaction_successful = False # <--- 新增一个标志
        if self.merchant_type == "normal":
            self.game.current_game_state = STATE_TRADING_NORMAL
            self.game.current_interacting_merchant = self
            self.game.current_interacting_player = player
            interaction_successful = True # <--- 标记成功
        elif self.merchant_type == "advanced":
            if self.game.adv_merchant_unlocked:
                self.game.current_game_state = STATE_TRADING_ADVANCED
                self.game.current_interacting_merchant = self
                self.game.current_interacting_player = player
                print("进入高级商人交易界面。")
                interaction_successful = True # <--- 标记成功
            else:
                print("高级商人似乎还没准备好交易...")
        return interaction_successful # <--- 返回交互是否成功启动
class Bomb(pygame.sprite.Sprite):
    def __init__(self, game, grid_x, grid_y, placer): # placer是放置炸弹的玩家
        super().__init__()
        self.game = game
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.placer = placer # 记录谁放的炸弹，可能用于得分或避免误伤自己（如果需要）
        self.image = load_image(BOMB_IMG_NAME, scale_to_grid=True)
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.grid_x * GRID_SIZE, self.grid_y * GRID_SIZE)
        self.spawn_time = pygame.time.get_ticks() # 记录放置时间
        self.fuse_time = BOMB_TIMER # 倒计时长

    def update(self):
        if pygame.time.get_ticks() - self.spawn_time > self.fuse_time:
            self.explode()

    def explode(self):
        print(f"炸弹在 ({self.grid_x}, {self.grid_y})爆炸!")
        # 创建爆炸效果精灵
        explosion = Explosion(self.game, self.grid_x, self.grid_y)
        self.game.all_sprites.add(explosion)
        self.game.effects_group.add(explosion) # 假设有一个effects_group用于管理这类效果

        # 对爆炸范围内的对象造成伤害
        # 爆炸中心是 (self.grid_x, self.grid_y)
        # 影响半径是 BOMB_EXPLOSION_RADIUS
        for r_offset in range(-BOMB_EXPLOSION_RADIUS, BOMB_EXPLOSION_RADIUS + 1):
            for c_offset in range(-BOMB_EXPLOSION_RADIUS, BOMB_EXPLOSION_RADIUS + 1):
                # 只处理曼哈顿距离（或圆形，但格子游戏用方形范围更简单）
                # if abs(r_offset) + abs(c_offset) > BOMB_EXPLOSION_RADIUS: # 菱形范围
                #    continue
                target_grid_x = self.grid_x + c_offset
                target_grid_y = self.grid_y + r_offset

                # 伤害怪物
                for monster in self.game.monsters_group:
                    if monster.grid_x == target_grid_x and monster.grid_y == target_grid_y:
                        # 炸弹造成的伤害，攻击者可以设为None或这个Bomb对象自身
                        monster.take_damage(BOMB_DAMAGE, self) # 传递Bomb作为攻击者

                # 伤害玩家 (包括放置者)
                for player_sprite in [self.game.player1, self.game.player2]:
                    if player_sprite.grid_x == target_grid_x and player_sprite.grid_y == target_grid_y:
                        print(f"炸弹波及玩家在 ({target_grid_x},{target_grid_y})")
                        player_sprite.take_damage(BOMB_DAMAGE)

                # 破坏可破坏的墙壁
                for b_wall in self.game.breakable_walls_group:
                    if b_wall.grid_x == target_grid_x and b_wall.grid_y == target_grid_y:
                        print(f"炸弹摧毁了可破坏的墙壁在 ({target_grid_x},{target_grid_y})")
                        b_wall.kill() # 直接移除

        self.kill() # 炸弹自身消失

class Explosion(pygame.sprite.Sprite):
    def __init__(self, game, grid_x, grid_y):
        super().__init__()
        self.game = game
        self.grid_x = grid_x
        self.grid_y = grid_y

        self.frames = []
        # 加载爆炸序列帧 (如果使用动画)
        if EXPLOSION_FRAME_COUNT > 0:
            for i in range(EXPLOSION_FRAME_COUNT):
                filename = f"{EXPLOSION_IMG_NAME_PREFIX}{i}.png"
                try:
                    frame = load_image(filename, scale_to_grid=True) # 爆炸效果可以覆盖整个格子
                    # 调整爆炸效果大小，使其覆盖半径
                    # 例如，如果半径是1，爆炸效果应该是3x3格子大小
                    explosion_pixel_size = GRID_SIZE * (2 * BOMB_EXPLOSION_RADIUS + 1)
                    frame = pygame.transform.scale(frame, (explosion_pixel_size, explosion_pixel_size))
                    self.frames.append(frame)
                except Exception as e: # 使用更通用的异常捕获
                    print(f"加载爆炸帧 {filename} 失败: {e}")
                    # 如果某一帧加载失败，可以跳过或使用占位符
                    pass # 或者添加一个占位符帧
            if not self.frames: # 如果没有成功加载任何帧
                self.create_placeholder_explosion()
        else: # 使用单张静态爆炸图片
            # filename = EXPLOSION_STATIC_IMG_NAME
            # self.frames.append(load_image(filename, scale_to_grid=True)) # 需要在settings中定义
            self.create_placeholder_explosion()


        self.current_frame_index = 0
        self.image = self.frames[self.current_frame_index] if self.frames else pygame.Surface((GRID_SIZE,GRID_SIZE))
        self.rect = self.image.get_rect()
        # 调整爆炸效果的中心点到炸弹爆炸的格子中心
        # 考虑爆炸效果图片本身的大小
        self.rect.centerx = self.grid_x * GRID_SIZE + GRID_SIZE // 2
        self.rect.centery = self.grid_y * GRID_SIZE + GRID_SIZE // 2

        self.last_frame_update = pygame.time.get_ticks()
        self.animation_speed = EXPLOSION_ANIMATION_SPEED
        self.duration = EXPLOSION_FRAME_COUNT * self.animation_speed if EXPLOSION_FRAME_COUNT > 0 else EXPLOSION_STATIC_DURATION
        self.spawn_time = pygame.time.get_ticks()

    def create_placeholder_explosion(self):
        """创建一个简单的占位符爆炸效果（例如一个红色闪烁方块）"""
        print("创建占位符爆炸效果，因为动画帧加载失败或未配置。")
        size = GRID_SIZE * (2 * BOMB_EXPLOSION_RADIUS + 1)
        placeholder_frame = pygame.Surface((size, size), pygame.SRCALPHA)
        placeholder_frame.fill((255, 100, 0, 150)) # 半透明橙红色
        self.frames = [placeholder_frame, pygame.Surface((size, size), pygame.SRCALPHA)] # 闪烁用
        self.duration = 500 # 占位符持续时间
        self.animation_speed = self.duration // 2
    def update(self):
        now = pygame.time.get_ticks()
        # 动画逻辑
        if self.frames and EXPLOSION_FRAME_COUNT > 0: # 序列帧动画
            if now - self.last_frame_update > self.animation_speed:
                self.last_frame_update = now
                self.current_frame_index += 1
                if self.current_frame_index >= len(self.frames):
                    self.kill() # 动画播放完毕
                else:
                    self.image = self.frames[self.current_frame_index]
        elif self.frames and EXPLOSION_FRAME_COUNT == 0: # 静态图片持续显示
             if now - self.spawn_time > self.duration:
                 self.kill()
        elif not self.frames: # 如果完全没有帧（比如占位符也没创建成功）
            self.kill()


class BreakableWall(pygame.sprite.Sprite):
    def __init__(self, game, grid_x, grid_y):
        super().__init__()
        self.game = game
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.image = load_image(WALL_BREAKABLE_IMG_NAME, scale_to_grid=True)
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.grid_x * GRID_SIZE, self.grid_y * GRID_SIZE)
        # 可破坏墙壁也应该在初始时加入到self.game.walls组，以实现碰撞
        # 它有一个单独的组 self.game.breakable_walls_group 用于被炸弹检测
    

    def kill(self): # 重写 kill 方法
        print(f"可破坏墙壁在 ({self.grid_x}, {self.grid_y}) 被摧毁，尝试生成传送门...")
    
        is_final_trigger = False
    # 假设右下角的可破坏墙壁 (例如地图最右下角是 (15,11) for a 16x12 map)
    # 你需要根据你的地图大小调整这个坐标
        if self.grid_x == (SCREEN_WIDTH // GRID_SIZE - 2) and self.grid_y == (SCREEN_HEIGHT // GRID_SIZE - 1): # 倒数第二列，最后一行
            print("这是通往BOSS的传送门生成点！")
            is_final_trigger = True

        portal_door = Door(self.game, self.grid_x, self.grid_y, 
                       pair_id=FINAL_PORTAL_ID, # 给它一个特殊ID
                       is_portal=True, 
                       is_final_portal_trigger=is_final_trigger) # 设置标记
        portal_door.set_state(True)

        self.game.all_sprites.add(portal_door)
        self.game.doors_group.add(portal_door)
        print(f"传送门在 ({self.grid_x}, {self.grid_y}) 已生成并激活。Final trigger: {is_final_trigger}")
        super().kill()

    def update(self):
        pass
# --- 新增 Potion 类 ---
class Potion(pygame.sprite.Sprite):
    def __init__(self, game, grid_x, grid_y, image_filename, potion_type, effect_value):
        super().__init__()
        self.game = game
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.potion_type = potion_type # "health", "attack"
        self.effect_value = effect_value # 效果数值 (例如治疗量, 攻击增加量)

        self.image = load_image(image_filename, scale_to_grid=False) # 药水图片通常不需要占满格子
        # 可以根据需要调整药水图片大小，例如：
        # target_potion_size = GRID_SIZE // 2
        # self.image = pygame.transform.scale(self.image, (target_potion_size, target_potion_size))
        self.rect = self.image.get_rect()
        self.rect.centerx = self.grid_x * GRID_SIZE + GRID_SIZE // 2
        self.rect.centery = self.grid_y * GRID_SIZE + GRID_SIZE // 2

    def apply_effect(self, player):
        """将药水效果应用给玩家"""
        player_id = "P1" if player.control_keys['up'] == pygame.K_w else "P2"
        if self.potion_type == "health":
            player.health += self.effect_value
            print(f"玩家 {player_id} 使用了生命药水，回复了 {self.effect_value} 点生命。当前生命: {player.health}")
        elif self.potion_type == "attack":
            player.attack_power += self.effect_value
            print(f"玩家 {player_id} 使用了攻击药水，攻击力增加了 {self.effect_value}。当前攻击力: {player.attack_power}")
        self.kill() # 药水被使用后消失

    def update(self):
        pass

class HealthPotion(Potion):
    def __init__(self, game, grid_x, grid_y):
        super().__init__(game, grid_x, grid_y, ITEM_HEALTH_POTION_IMG_NAME, "health", HEALTH_POTION_HEAL_AMOUNT)

class AttackPotion(Potion):
    def __init__(self, game, grid_x, grid_y):
        super().__init__(game, grid_x, grid_y, ITEM_ATTACK_POTION_IMG_NAME, "attack", ATTACK_POTION_BUFF_AMOUNT)
# --- 新增 Switch 类 ---
class Switch(pygame.sprite.Sprite):
    def __init__(self, game, grid_x, grid_y, switch_id, initial_state='off'):
        super().__init__()
        self.game = game
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.switch_id = switch_id # 开关的唯一标识

        self.image_on = load_image(SWITCH_ON_IMG_NAME, scale_to_grid=True)
        self.image_off = load_image(SWITCH_OFF_IMG_NAME, scale_to_grid=True)

        self.state = initial_state # 'off', 'pending_monsters', 'on'
        self._update_image() # 根据初始状态设置图片

        self.rect = self.image.get_rect()
        self.rect.topleft = (self.grid_x * GRID_SIZE, self.grid_y * GRID_SIZE)

        self.monsters_to_defeat_count = 0 # 需要击败的怪物数量 (在生成怪物时设置)
        self.linked_monsters = pygame.sprite.Group() # 用于追踪这个开关生成的特定怪物

    def _update_image(self):
        """根据当前状态更新开关的图片"""
        if self.state == 'on':
            self.image = self.image_on
        else: # 'off' 或 'pending_monsters' 都显示为 off 状态的图片
            self.image = self.image_off

    def interact(self, player):
        """玩家与开关互动"""
        if self.state == 'off': # 只有在 'off' 状态才能被第一次激活
            player_id = "P1" if player.control_keys['up'] == pygame.K_w else "P2"
            print(f"玩家 {player_id} 激活了开关 {self.switch_id} at ({self.grid_x},{self.grid_y})!")
            self.state = 'pending_monsters' # 进入等待怪物被击败的状态
            self._update_image() # 虽然图片可能还是off，但状态变了
            # 通知 Game 对象生成怪物
            self.game.spawn_monsters_for_switch(self)
            return True
        elif self.state == 'pending_monsters':
            print(f"开关 {self.switch_id} 正在等待怪物被清除...")
            return False
        elif self.state == 'on':
            print(f"开关 {self.switch_id} 已经被完全激活了。")
            return False
        return False

    def monster_defeated(self, monster):
        """当一个与此开关关联的怪物被击败时调用"""
        if self.state == 'pending_monsters' and monster in self.linked_monsters:
            self.linked_monsters.remove(monster) # 从追踪列表中移除
            self.monsters_to_defeat_count = len(self.linked_monsters.sprites()) # 更新剩余数量
            print(f"开关 {self.switch_id} 的一个关联怪物被击败，剩余 {self.monsters_to_defeat_count} 个。")
            if self.monsters_to_defeat_count <= 0:
                self.activate_fully()
        
    def activate_fully(self):
        """所有关联怪物被击败后，完全激活开关"""
        print(f"开关 {self.switch_id} 的所有怪物已被清除！开关完全激活！")
        self.state = 'on'
        self._update_image()
        # 在这里可以触发更进一步的事件，比如通知Game对象高级商人解锁
        self.game.event_switch_fully_activated(self)


    def update(self):
        # Switch 的状态主要由交互和怪物击败事件驱动
        pass
class TalismanPickup(pygame.sprite.Sprite):
    def __init__(self, game, grid_x, grid_y):
        super().__init__()
        self.game = game
        self.grid_x = grid_x
        self.grid_y = grid_y

        self.image = load_image(ITEM_TALISMAN_PICKUP_IMG_NAME, scale_to_grid=True) # 或者 scale_to_grid=False 如果你想自定义大小
        # 如果 scale_to_grid=False，你可能想调整它的大小，让它看起来像一个物品而不是占满格子
        # if not scale_to_grid:
        #     self.image = pygame.transform.scale(self.image, (GRID_SIZE // 2, GRID_SIZE // 2)) # 例如半格大小

        self.rect = self.image.get_rect()
        # 定位，可以放在格子中央或左上角
        self.rect.centerx = self.grid_x * GRID_SIZE + GRID_SIZE // 2
        self.rect.centery = self.grid_y * GRID_SIZE + GRID_SIZE // 2
        # 或者 self.rect.topleft = (self.grid_x * GRID_SIZE, self.grid_y * GRID_SIZE)

    def apply_random_talisman_effect(self, player):
        """对玩家应用一个随机的符箓效果，并自我销毁"""
        player_id_str = "P1" if player.control_keys['up'] == pygame.K_w else "P2"
        
        possible_effects = ["crit_chance", "crit_damage", "dodge_chance"]
        chosen_effect = random.choice(possible_effects)
        
        talisman_applied_msg = f"玩家 {player_id_str} 拾取了符箓，增强了 "
        if chosen_effect == "crit_chance":
            increase = round(random.uniform(TALISMAN_CRIT_CHANCE_INCREASE_MIN, TALISMAN_CRIT_CHANCE_INCREASE_MAX), 3)
            player.crit_chance += increase
            player.crit_chance = min(player.crit_chance, 1.0)
            talisman_applied_msg += f"暴击率 {increase*100:.1f}%！当前暴击率: {player.crit_chance*100:.1f}%"
        elif chosen_effect == "crit_damage":
            increase = round(random.uniform(TALISMAN_CRIT_DAMAGE_INCREASE_MIN, TALISMAN_CRIT_DAMAGE_INCREASE_MAX), 2)
            player.crit_damage_multiplier += increase
            talisman_applied_msg += f"暴击伤害倍率 {increase*100:.0f}%！当前暴击伤害: {player.crit_damage_multiplier*100:.0f}%"
        elif chosen_effect == "dodge_chance":
            increase = round(random.uniform(TALISMAN_DODGE_CHANCE_INCREASE_MIN, TALISMAN_DODGE_CHANCE_INCREASE_MAX), 3)
            player.dodge_chance += increase
            player.dodge_chance = min(player.dodge_chance, 0.9)
            talisman_applied_msg += f"闪避率 {increase*100:.1f}%！当前闪避率: {player.dodge_chance*100:.1f}%"
        
        print(talisman_applied_msg)
        self.kill() # 符箓被拾取后消失

    def update(self):
        # 符箓拾取物通常是静态的
        pass
class Boss(Monster): # 继承自 Monster
    def __init__(self, game, grid_x, grid_y, image_filename):
        # 调用父类 Monster 的 __init__，但传入BOSS特定的属性
        # 我们不需要 spawned_by_switch 参数，所以设为 None
        super().__init__(game, grid_x, grid_y, image_filename, spawned_by_switch=None)
        
        self.health = BOSS_HEALTH         # 从 settings.py 获取
        self.attack_power = BOSS_ATTACK_POWER # 从 settings.py 获取
        self.gold_value = BOSS_GOLD_DROP    # 从 settings.py 获取
        
        # BOSS特有的属性或行为可以在这里添加
        self.is_boss = True # 一个标记，方便识别
        print(f"最终BOSS在 ({self.grid_x}, {self.grid_y}) 生成！HP: {self.health}, ATK: {self.attack_power}")

    def take_damage(self, amount, attacker=None):
        # 调用父类的 take_damage 处理伤害和普通怪物死亡逻辑
        super().take_damage(amount, attacker)
        
        # 在这里添加BOSS被击败后的特殊逻辑
        if self.health <= 0 and not self.game.current_game_state == STATE_GAME_WON: # 确保只触发一次
            print("最终BOSS已被击败！游戏胜利！")
            # 可以在这里给予玩家最终奖励等
            if isinstance(attacker, Player): # 或者根据谁打出最后一击
                # attacker.add_huge_score()
                pass

            self.game.trigger_game_won() # 通知 Game 对象游戏胜利

# 你可以继续在这里添加其他精灵类
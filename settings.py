# settings.py
_author_='WenAlis'
import pygame
import os

# --- 常量定义 ---
# 屏幕尺寸
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
GRID_SIZE = 64
FPS = 60

# 颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (128, 128, 128) # 用于背景格子
LIGHT_GREY = (200, 200, 200) # 用于背景格子
DARK_GREY = (50,50,50) # 用于网格线

# 图片资源路径
# 使用 os.path.join 来确保路径在不同操作系统上的兼容性
BASE_IMG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pic")

COVER_BACKGROUND_IMG_NAME = "cover_background.png"
# 玩家设置
PLAYER_IMG_NAME_1 = "user1.png"
PLAYER_IMG_NAME_2 = "user2.png" # 假设你也有user2.png

# 玩家初始格子坐标 (确保这些坐标在地图上是空地 '0')
PLAYER_1_START_GRID_X = 1 # 例如，第1列 (从0开始)
PLAYER_1_START_GRID_Y = 1# 例如，第1行 (从0开始)

PLAYER_2_START_GRID_X = 14 # 例如，第3列
PLAYER_2_START_GRID_Y = 1 # 例如，第1行

# --- 新增：玩家受击抖动设置 (可以和怪物一样，或单独设置) ---
PLAYER_SHAKE_DURATION = 150
PLAYER_SHAKE_INTENSITY = 4

# 地图图块名称 (示例，我们会用到 wall.png)
TILE_WALL_IMG_NAME = "wall.png"

# 物品图片名称
ITEM_COIN_IMG_NAME = "coin.png" # 新增
ITEM_HEALTH_POTION_IMG_NAME = "lifepotion.png"    # 新增
ITEM_ATTACK_POTION_IMG_NAME = "attackpotion.png"  # 新增
# --- 新增：药水效果设置 ---
HEALTH_POTION_HEAL_AMOUNT = 50  # 生命药水回复量
ATTACK_POTION_BUFF_AMOUNT = 10   # 攻击药水增加量
# 怪物图片名称
MONSTER_SLIME_IMG_NAME = "sboss.png"
MONSTER_MEDIUM_IMG_NAME = "mboss.png"
# 怪物设置
MONSTER_HEALTH = 30 # 示例怪物血量
MONSTER_ATTACK_POWER = 5 # 示例怪物攻击力
MONSTER_SHAKE_DURATION = 150 # 怪物震动持续时间 (毫秒)
MONSTER_SHAKE_INTENSITY = 4 # 怪物震动幅度 (像素)
MONSTER_GOLD_DROP = 5 # 怪物被击败时掉落的金币数量

# --- 新增：中等怪物设置 ---
MONSTER_MEDIUM_HEALTH = 100
MONSTER_MEDIUM_ATTACK_POWER = 20
MONSTER_MEDIUM_GOLD_DROP = 80 # 中等怪掉更多金币 (可选)

BUTTON_ON_IMG_NAME = "button_on.png"
BUTTON_OFF_IMG_NAME = "button_off.png"
DOOR_IMG_NAME = "door.png"
BUTTON_DOOR_PAIR_ID = 1 # 用于关联按住生效的按钮和它控制的门
# --- 新增：商人设置 ---
MERCHANT_NORMAL_IMG_NAME = "merchant1.png"
MERCHANT_ADVANCED_IMG_NAME = "merchant2.png" 

INTERACTION_KEY = pygame.K_e # 玩家与商人等互动的按键 (E键)
# --- 新增：炸弹和爆炸设置 ---
BOMB_IMG_NAME = "bomb.png"
EXPLOSION_IMG_NAME_PREFIX = "explosion_anim_" # 如果用序列帧，例如 explosion_anim_0.png, _1.png ...
EXPLOSION_FRAME_COUNT = 2 # 爆炸动画的帧数 (如果用序列帧)
EXPLOSION_ANIMATION_SPEED = 1000 # 每帧持续时间 (毫秒)
# 如果用单张爆炸图片: EXPLOSION_STATIC_IMG_NAME = "explosion.png"
EXPLOSION_STATIC_DURATION = 1000 # 单张爆炸图片显示时长

BOMB_TIMER = 3000      # 炸弹爆炸倒计时 (3秒)
BOMB_PLACE_KEY_P1 = pygame.K_q  # 玩家1放置炸弹的按键 (Q)
BOMB_PLACE_KEY_P2 = pygame.K_f  # 玩家2放置炸弹的按键 (F)
INITIAL_BOMBS = 3        # 每个玩家初始的炸弹数量
BOMB_DAMAGE = 50         # 炸弹对怪物和玩家造成的伤害
BOMB_EXPLOSION_RADIUS = 1 # 爆炸影响的格子半径 (0代表只影响本格子, 1代表本格子及周围一圈)
# --- 新增：可破坏墙壁设置 ---
WALL_BREAKABLE_IMG_NAME = "wall_breakable.png"
# --- 新增：开关和高级商人任务相关设置 ---
SWITCH_OFF_IMG_NAME = "switch_off.png"
SWITCH_ON_IMG_NAME = "switch_on.png"
MERCHANT1_SPEND_THRESHOLD_FOR_SWITCH = 30 # 在普通商人处消费达到这个数额才生成开关
ADV_MERCHANT_SWITCH_ID = "adv_merchant_unlock_switch" # 此开关的唯一ID
# 开关生成的位置 (格子坐标, 需要你在地图上找一个合适空地)
# 这个位置应该是固定的，或者通过某种逻辑确定
SWITCH_SPAWN_GRID_X = 13 # 示例 X
SWITCH_SPAWN_GRID_Y = 7 # 示例 Y

ADV_MERCHANT_SPAWN_GRID_X = 1  # <--- 新增：示例 X (请根据你的地图调整)
ADV_MERCHANT_SPAWN_GRID_Y = 1  # <--- 新增：示例 Y (请根据你的地图调整)

STATE_PLAYING = 0
STATE_TRADING_NORMAL = 1
STATE_TRADING_ADVANCED = 2
STATE_MENU = 3  # <--- 新增：菜单/封面状态
STATE_GAME_WON = 4   
STATE_GAME_OVER = 5         # <--- 新增：游戏失败/结束状态

# --- 符箓设置 ---
ITEM_TALISMAN_PICKUP_IMG_NAME = "middlegift.png"
TALISMAN_HEALTH_COST = 30 # 购买一个随机符箓消耗的生命值

TALISMAN_CRIT_CHANCE_INCREASE_MIN = 0.08 # 随机增加暴击率的最小值 (3%)
TALISMAN_CRIT_CHANCE_INCREASE_MAX = 0.18 # 随机增加暴击率的最大值 (7%)

TALISMAN_CRIT_DAMAGE_INCREASE_MIN = 0.2 # 随机增加暴击伤害倍率的最小值 (0.1 表示从1.5到1.6)
TALISMAN_CRIT_DAMAGE_INCREASE_MAX = 0.4 # 随机增加暴击伤害倍率的最大值

TALISMAN_DODGE_CHANCE_INCREASE_MIN = 0.15 # 随机增加闪避率的最小值 (2%)
TALISMAN_DODGE_CHANCE_INCREASE_MAX = 0.25 # 随机增加闪避率的最大值

# --- 新增：最终BOSS设置 ---
BOSS_HEALTH = 1000           # <--- 新增：BOSS血量 (例如，比中级怪高很多)
BOSS_ATTACK_POWER = 50      # <--- 新增：BOSS攻击力
BOSS_GOLD_DROP = 100        # <--- 新增：BOSS掉落金币 (可选)
BOSS_SPAWN_GRID_X = 3       # <--- 新增：BOSS生成位置X (请根据你的地图或BOSS战场地调整)
BOSS_SPAWN_GRID_Y = 10       # <--- 新增：BOSS生成位置Y
FINAL_PORTAL_ID = "boss_portal" # <--- 新增：用于识别触发BOSS战的传送门的特殊ID 
BOSS_FINAL_IMG_NAME="bboss.png"

# --- 新增：绝境爆发属性增益值 ---
SURVIVOR_BONUS_HEALTH = 500
SURVIVOR_BONUS_ATTACK = 50
SURVIVOR_BONUS_DODGE = 0.30 # 30%
SURVIVOR_BONUS_CRIT = 0.30  # 30%


# STATE_DIALOGUE = 3 # 如果有问答NPC
# 游戏状态 (如果我们之后需要更复杂的状态管理)
# STATE_PLAYING = "playing"
# STATE_GAME_OVER = "game_over"
# STATE_MENU = "menu"

# 辅助函数，用于加载图片并进行错误处理
def load_image(filename, scale_to_grid=True, base_path=BASE_IMG_PATH):
    """加载图片，可选择缩放到格子大小，并进行错误处理"""
    full_path = os.path.join(base_path, filename)
    try:
        image = pygame.image.load(full_path)
        if image.get_alpha() is None: # 检查图片是否有alpha通道
            image = image.convert() # 如果没有，转换为非alpha格式
        else:
            image = image.convert_alpha() # 如果有，转换为带alpha的格式以优化性能

        if scale_to_grid:
            image = pygame.transform.scale(image, (GRID_SIZE, GRID_SIZE))
        return image
    except pygame.error as e:
        print(f"错误：无法加载图片 '{filename}' 从路径 '{full_path}'。错误信息: {e}")
        # 返回一个占位符表面
        placeholder = pygame.Surface((GRID_SIZE, GRID_SIZE))
        placeholder.fill((255, 0, 0)) # 红色方块
        pygame.draw.rect(placeholder, WHITE, placeholder.get_rect(), 2)
        font = pygame.font.SysFont(None, 18)
        text_surf = font.render("ERR", True, WHITE)
        text_rect = text_surf.get_rect(center=placeholder.get_rect().center)
        placeholder.blit(text_surf, text_rect)
        return placeholder
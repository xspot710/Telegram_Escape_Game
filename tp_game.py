import json
import os
from PIL import Image
import subprocess

# 確保state中 password跟condition不會同時出現
# 理論上也不該同時出現
# 同時出現會影響 make_move的判斷
class TPGame:
    def __init__(self, user_id, language="zh"):
        self.user_id = user_id
        self.FilePath = 'saves/states_{user_id}.json'
        if os.path.exists(self.FilePath):
            with open(self.FilePath, 'r', encoding='utf-8') as f:
                self.states = json.load(f)   
            self.current_state_id = self.states[-1]["current_state"]   
        else:
            with open('saves/states.json', 'r', encoding='utf-8') as f:
                self.states = json.load(f)   
            self.current_state_id = self.states[-1]["current_state"]   
        self.language = language
    
    def save(self):
        with open(self.FilePath, 'r', encoding='utf-8') as f:
            json.dump(self.states, f)

    def get_current_state(self):
        for state in self.states:
            if state["id"] == self.current_state_id:
                self.state_reach(state)
                return state
        return None

    def if_condition(self, state_id, conditionKey):
        for state in self.states:
            if state["id"] == state_id:
                condi_state = state
                break
        value = condi_state[conditionKey]
        if isinstance(value, bool):
            return value
        if value == 0: # 因為playerReach是計次的，所以如果不是純的布林值的話，得用數字判斷。
            return False 
        else:
            return True
        
    def state_reach(self, state):
        if "playerReach" in state:
            reach_time = state["playerReach"] + 1
            state["playerReach"] = int(reach_time)

    def get_possible_moves(self):
        state = self.get_current_state()
        if state:
            return state["possibleMoves"][self.language]
        return []
    
    def make_move(self, action) -> bool:
        state = self.get_current_state()
        if not state:
            return None
        if self.current_state_id == "5_0":
            return "遊戲結束"
        for move in state["possibleMoves"][self.language]:
            if move["action"] != action:
                continue  
            
            if "condition" in move:
                conditionKey = move["condition"]["conditionKey"]
                if conditionKey == 'unlocked':
                    condition = self.if_condition(move["condition"]["state"], conditionKey)
                elif conditionKey == 'playerReach':
                    condition = self.if_condition(move["condition"]["state"], conditionKey)
                self.current_state_id = move["nextStateIfConditionTrue"] if condition else move["nextStateIfConditionFalse"]
            else:
                self.current_state_id = move["nextState"]
            break 
        # 對於密碼的State做特殊處理
        if "password" in state:
            state["playersAttempts"] += 1
            valid_pwd = str(state["password"])
            pwd = str(action)
            if valid_pwd == pwd: # 密碼正確
                state["unlocked"] = True
                self.current_state_id = state["unlockedState"]
            else:
                return False # 輸入密碼失敗
        self.states[-1]["current_state"] = self.current_state_id # 這個在儲存當前的進度，存在init State的current_state裡
        return True 

    def display_with_image(self):
        state = self.get_current_state()
        image_path = os.path.join("images", state["image"])  
        state_description = state["description"][self.language]

        print(f"\n位置: {state['locate']}")
        print(state_description)
        state_actions = '\n'.join([f"- {move['action']}" for move in state["possibleMoves"][self.language]])
        print(f"\n你可以选择:\n{state_actions}")

        # 检查图像文件是否存在，然后打開它
        if os.path.exists(image_path):
            img = Image.open(image_path)
            img.show() 
        else:
            print(f"⚠️ 找不到图像: {image_path}")

    def tg_display(self):
        state = self.get_current_state()
        image = state["image"]
        description = state["description"][self.language]
        actions = state["possibleMoves"][self.language]
        return image, description, actions

    def display(self):
        state = self.get_current_state()
        image_path = os.path.join("images", state["image"])
        state_description = state["description"][self.language]

        print(f"\n位置: {state['locate'][self.language]}")
        print(state_description)
        state_actions = '\n'.join([f"- {move['action']}" for move in state["possibleMoves"][self.language]])

        # 圖片轉換成ASCII
        if os.path.exists(image_path):
            try:
                command = ["ascii-image-converter", "--width=100", image_path]
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                print(result.stdout)  # 輸出ASCII
            except subprocess.CalledProcessError as e:
                print("⚠️ 轉換失敗：")
                print(e.stderr)
        else:
            print(f"⚠️ 找不到圖片: {image_path}")
        
        print(f"\n你可以选择:\n{state_actions}")


# CLI 版本的遊戲執行函數
def cli_game_loop():
    user_id = "local_player"
    game = TPGame(user_id)

    print("🎮 歡迎來到密室逃脫遊戲！")
    print("輸入動作來進行遊戲，輸入 'exit' 來離開。")
    
    while True:
        game.display()
        action = input("\n請輸入你的動作: ").strip()
        if action.lower() == "exit":
            print("遊戲結束，期待你的下一次挑戰！")
            break
        result = game.make_move(action)
        if result == "遊戲結束":
            print("🎉 恭喜你成功逃脫！")
            break
        elif not result:
            print("❌ 密碼錯誤或行動無效，請重試！")

# 判斷是否是主程式
if __name__ == "__main__":
    cli_game_loop()
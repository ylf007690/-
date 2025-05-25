import ntptime
import time
from machine import RTC, Pin
import network
import socket

class ESP32NetworkTime:
    def __init__(self, ssid, password, timezone=8, ntp_server="pool.ntp.org"):
        """
        初始化网络和时间类
        
        参数:
            ssid: WiFi名称
            password: WiFi密码
            timezone: 时区偏移（中国为+8）
            ntp_server: NTP服务器地址
        """
        self.ssid = ssid
        self.password = password
        self.timezone = timezone
        self.ntp_server = ntp_server
        self.sta_if = network.WLAN(network.STA_IF)
        self.rtc = RTC()
        
        
        
    def connect(self):
        """连接到WiFi网络"""
        if not self.sta_if.isconnected():
            print('正在连接到网络...')
            self.sta_if.active(True)
            self.sta_if.connect(self.ssid, self.password)
            
            # 增加等待时间和重试次数
            max_retries = 30  # 15秒等待时间
            for _ in range(max_retries):
                if self.sta_if.isconnected():
                    break
                time.sleep(0.5)
                
        if self.sta_if.isconnected():
            print('网络连接成功!')
            print('IP地址:', self.sta_if.ifconfig()[0])
            return True
        else:
            print('网络连接失败!')
            return False
            
    def disconnect(self):
        """断开WiFi连接"""
        if self.sta_if.isconnected():
            self.sta_if.disconnect()
        self.sta_if.active(False)
        print('已断开网络连接')
        
    def sync_ntp_time(self, retries=3):
        """
        从NTP服务器同步时间
        
        参数:
            retries: 重试次数
            
        返回:
            bool: 是否同步成功
        """
        if not self.sta_if.isconnected():
            print("未连接网络，无法同步NTP")
            return False
            
        # 备份原始NTP服务器设置
        original_ntp = ntptime.host
        
        # 尝试使用自定义NTP服务器
        ntptime.host = self.ntp_server
        
        for attempt in range(retries):
            try:
                print(f"尝试NTP同步 (尝试 {attempt+1}/{retries})...")
                ntptime.settime()
                print("NTP时间同步成功")
                return True
            except Exception as e:
                print(f"NTP同步失败: {e}")
                time.sleep(1)  # 等待1秒后重试
                
        # 恢复原始NTP服务器设置
        ntptime.host = original_ntp
        return False
            
    def get_time(self, sync=False):
        """
        获取当前时间
        
        参数:
            sync: 是否强制同步NTP时间
            
        返回:
            格式化的时间字符串 (YYYY-MM-DD HH:MM:SS) 或 None
        """
        if sync or not self.sta_if.isconnected():
            if not self.connect():
                return None
            if not self.sync_ntp_time():
                print("警告: 使用本地RTC时间，可能不准确")
                # 即使同步失败也返回本地时间
                
        tm = self.rtc.datetime()
        
        # 应用时区偏移
        tm = list(tm)
        tm[4] += self.timezone  # 小时数增加时区偏移
        if tm[4] >= 24:
            tm[4] -= 24
            tm[2] += 1  # 天数增加
            
        # 格式化为字符串
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            tm[0], tm[1], tm[2], tm[4], tm[5], tm[6])
            
    def get_local_time(self):
        """
        获取RTC本地时间(不进行网络同步)
        
        返回:
            格式化的时间字符串 (YYYY-MM-DD HH:MM:SS)
        """
        tm = self.rtc.datetime()
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            tm[0], tm[1], tm[2], tm[4], tm[5], tm[6])

# 使用示例
if __name__ == "__main__":
    # 配置你的WiFi信息
    WIFI_SSID = "1611"
    WIFI_PASSWORD = "63558095"
    
    # 创建实例，可以尝试不同的NTP服务器
    ntp_servers = [
        "pool.ntp.org",           # 默认全球NTP池
        "cn.pool.ntp.org",        # 中国NTP池
        "ntp.aliyun.com",         # 阿里云NTP
        "time1.cloud.tencent.com" # 腾讯云NTP
    ]
    
    for server in ntp_servers:
        print(f"\n尝试使用NTP服务器: {server}")
        esp_net_time = ESP32NetworkTime(
            WIFI_SSID, 
            WIFI_PASSWORD, 
            timezone=8,
            ntp_server=server
        )
        
        # 连接到网络
        if esp_net_time.connect():
            # 获取时间(自动同步)
            current_time = esp_net_time.get_time(sync=True)
            print("当前网络时间:", current_time)
        # 断开网络
            esp_net_time.disconnect()
            break  # 如果成功就停止尝试            
            
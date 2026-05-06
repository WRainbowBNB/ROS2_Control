import rclpy
from rclpy.node import Node
import serial
import struct
from std_msgs.msg import UInt8, Float32, Int8, Bool
import sys

class STM32BridgeNode(Node):
	def __init__(self):
		super().__init__('stm32_bridge_node')
		
		self.ser = None
		#开串口
		try:
			self.ser = serial.Serial('/dev/ttyUSB0', 115200, timeout = 0)
			self.get_logger().info("串口已连接")
		except Exception as e:
			self.get_logger().error(f"串口连接错误{e}")
			sys.exit(1)
		
		#俩订一发布,led_cmd是rqt用的，gpio_state是广播给别人用的
		self.create_subscription(Int8, 'cmd_led_switch', self.switch_callback, 10)
		self.create_subscription(Float32, 'cmd_led_brightness', self.brightness_callback, 10)
		self.gpio_state_pub = self.create_publisher(Bool, 'gpio_state', 10)
		self.create_timer(0.2, self.read_serial_data)
		self.rx_buffer = bytearray()
	
	#action回调0x01
	def switch_callback(self, msg):
		#取rqt发来的数据
		action = msg.data
		#组装列表
		frame = [0x5A, 0xA5, 0x01, action]
		#计算校验和,我去python这么方便的吗
		check_sum = sum(frame) & 0xFF
		frame.append(check_sum)
		#发送发送
		self.ser.write(bytearray(frame))
		self.get_logger().info(f'Action指令发送完毕：{[hex(x) for x in frame]}')
	
	#val回调0x02
	def brightness_callback(self, msg):
		#取rqt的数据
		val = list(struct.pack('<f', msg.data))
		#组装列表
		frame = [0x5A, 0xA5, 0x02] + val
		#计算校验和
		check_sum = sum(frame) & 0xFF
		frame.append(check_sum)
		#发送发送
		self.ser.write(bytearray(frame))
		self.get_logger().info(f'Val指令发送完毕：{[hex(x) for x in frame]}')
		
	def read_serial_data(self):
		#缓存有无数据，wok真方便啊
		if self.ser.in_waiting > 0:
			#读数据
			data = self.ser.read(self.ser.in_waiting)
			self.rx_buffer.extend(data)
		
			#处理数据
			while len(self.rx_buffer) >= 4:
				if self.rx_buffer[0] == 0x5A and self.rx_buffer[1] == 0xA5:
					frame = self.rx_buffer[:4]
					#计算校验位
					check_sum = (frame[0] + frame[1] +frame[2]) & 0xFF
					if check_sum == frame[3]:
						gpio_state = frame[2]
						#让发布者发布信息
						msg = Bool()
						msg.data = bool(gpio_state)
						self.gpio_state_pub.publish(msg)
						self.get_logger().info(f'收到gpio状态{"高电平" if gpio_state else "低电平"}')
						#去掉之前的四字节
						del self.rx_buffer[:4]
				
					else:
						#避免假帧头
						self.rx_buffer.pop(0)
						
				else:
					#窗口后移一位
					self.rx_buffer.pop(0)	
	
#ROS2入口
def main(args=None):
	rclpy.init(args=args)
	node = STM32BridgeNode()
	try:
		rclpy.spin(node)
	except KeyboardInterrupt:
		node.get_logger().info("节点被手动停止")
	finally:
		#关闭串口并销毁节点
		if node.ser is not None and node.ser.is_open:
			node.ser.close()
		node.destroy_node()
		rclpy.shutdown()

if __name__ == '__main__':
	main()

		
	
	
	
		

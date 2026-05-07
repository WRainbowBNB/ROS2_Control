import sys
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int8, Float32, Bool
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout
from PyQt6.QtCore import QTimer, pyqtSignal, QObject, Qt
from LED_UI import Ui_Dialog

#目标引脚电平状态显示
#绿色-高电平
STYLE_ON = """
background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                            fx:0.5, fy:0.5,
                            stop:0 #88ff88,
                            stop:1 #00aa00);
border-radius: 20px;
border: 1px solid #00ff00;
"""

#灰色-低电平
STYLE_OFF = """
background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                            fx:0.5, fy:0.5,
                            stop:0 #888888,
                            stop:1 #444444);
border-radius: 20px;
border: 1px solid #666666;
"""

#GUI节点
class GUINode(Node, QObject):
	gpio_signal = pyqtSignal(bool)
	
	def __init__(self):
		Node.__init__(self, 'GUI_node')
		QObject.__init__(self)
		self.create_subscription(Bool, 'gpio_state', self.gui_gpio_state_callback, 10)
		self.switch_pub = self.create_publisher(Int8, 'cmd_led_switch', 10)
		self.brightness_pub = self.create_publisher(Float32, 'cmd_led_brightness', 10)
	
	#传信号给自定义GUI界面	
	def gui_gpio_state_callback(self, msg):
		self.gpio_signal.emit(msg.data)


class MainWindow(QDialog, Ui_Dialog):
	def __init__(self):
		super().__init__()
		self.setupUi(self)
		self.gui_node = GUINode()
		self.ON.clicked.connect(self.ON_callback)
		self.OFF.clicked.connect(self.OFF_callback)
		self.Toggle.clicked.connect(self.Toggle_callback)
		self.brightness_controller.valueChanged.connect(self.Brightness_controller_callback)			
		self.gui_node.gpio_signal.connect(self.gpio_state_callback)
		self.led_action  = 0
		self.label_4.setAlignment(Qt.AlignmentFlag.AlignCenter)
		
	def ON_callback(self):
		msg = Int8()
		msg.data = 1
		self.led_action = msg.data
		self.gui_node.switch_pub.publish(msg)
	
	def OFF_callback(self):
		msg = Int8()
		msg.data = 0
		self.led_action = msg.data
		self.gui_node.switch_pub.publish(msg)

	def Toggle_callback(self):
		msg = Int8()
		if self.led_action == 1:
			msg.data = 0
		else:
			msg.data = 1
		self.led_action = msg.data
		self.gui_node.switch_pub.publish(msg)
	
	def Brightness_controller_callback(self, value):
		#换算换算
		brightness = value / 100.0
		self.label_4.setText(f"亮度：{brightness:.2f}")
		msg = Float32()
		msg.data = brightness
		self.gui_node.brightness_pub.publish(msg)
	
	def gpio_state_callback(self, msg):
		if msg:
			self.label.setStyleSheet(STYLE_ON)
		else:
			self.label.setStyleSheet(STYLE_OFF)
	
	def closeEvent(self, event):
	    self.gui_node.destroy_node()
	    event.accept()
	
#ROS2入口
def main(args=None):
	rclpy.init()
	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	#感觉像时间片
	timer = QTimer()
	timer.timeout.connect(lambda: rclpy.spin_once(window.gui_node, timeout_sec = 0))
	timer.start(10)
	
	app.exec()
	rclpy.shutdown()
	

if __name__ == '__main__':
	main()


import unittest
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.thinkcloud import deep_thinking

class TestDeepThinking(unittest.TestCase):
    
    def test_basic_deep_thinking(self):
        """测试基本深度思考功能"""
        question = "Python中列表和元组的区别是什么？"
        result = deep_thinking(question)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
    
    def test_complex_question(self):
        """测试复杂问题的深度思考"""
        question = "请详细解释Python中的GIL（全局解释器锁）对多线程性能的影响，并提供解决方案。"
        result = deep_thinking(question)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 50)  # 确保返回较长的回答
    
    def test_iterative_improvement(self):
        """测试迭代改进机制"""
        question = "如何优化Python代码的性能？"
        result1 = deep_thinking(question)
        result2 = deep_thinking(question)  # 第二次调用应该利用缓存或改进结果
        
        # 验证两次结果都是有效回答
        self.assertIsInstance(result1, str)
        self.assertIsInstance(result2, str)
        self.assertGreater(len(result1), 0)
        self.assertGreater(len(result2), 0)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试空输入
        with self.assertRaises(Exception):
            deep_thinking("")
        
        # 测试None输入
        with self.assertRaises(Exception):
            deep_thinking(None)

if __name__ == '__main__':
    unittest.main()
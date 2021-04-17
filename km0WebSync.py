from multiprocessing import freeze_support
from app.app import Application

if __name__ == '__main__':
  freeze_support()
  app = Application()
  app.start()
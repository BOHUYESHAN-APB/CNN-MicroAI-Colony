"""树莓派UI入口"""
from .app import PiCtkMvpApp

if __name__ == "__main__":
    app = PiCtkMvpApp()
    app.mainloop()

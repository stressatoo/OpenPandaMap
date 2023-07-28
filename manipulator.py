class Manipulator:
    def __init__(self, app):
        self.app = app
        self.selected_obj = None

        self.app.accept('arrow_left', self.move_left)
        self.app.accept('arrow_right', self.move_right)
        self.app.accept('arrow_up', self.move_up)
        self.app.accept('arrow_down', self.move_down)

    def select_object(self, obj):
        self.selected_obj = obj

    def move_left(self):
        if self.selected_obj:
            self.selected_obj.setX(self.selected_obj.getX() - 1)

    def move_right(self):
        if self.selected_obj:
            self.selected_obj.setX(self.selected_obj.getX() + 1)

    def move_up(self):
        if self.selected_obj:
            self.selected_obj.setY(self.selected_obj.getY() - 1)

    def move_down(self):
        if self.selected_obj:
            self.selected_obj.setY(self.selected_obj.getY() + 1)
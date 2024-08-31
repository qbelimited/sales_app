from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'admin', 'sales_manager', 'back_office', 'manager'
    is_active = db.Column(db.Boolean, default=True)

    branch = db.relationship('Branch', backref='users')

    def serialize(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'branch_id': self.branch_id,
            'role': self.role,
            'is_active': self.is_active
        }

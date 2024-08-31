from app import db

class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    ghpost_gps = db.Column(db.String(100), nullable=True)

    users = db.relationship('User', backref='branch', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'region': self.region,
            'ghpost_gps': self.ghpost_gps
        }

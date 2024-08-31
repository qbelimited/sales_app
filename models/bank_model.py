from app import db

class Bank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    branches = db.relationship('Branch', backref='bank', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'branches': [branch.serialize() for branch in self.branches]
        }

class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bank_id = db.Column(db.Integer, db.ForeignKey('bank.id'), nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'bank_id': self.bank_id
        }

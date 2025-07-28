#from sqlalchemy.orm import Session
#from app.db.session import SessionLocal
#from app.db.models.user import User
#from passlib.context import CryptContext

# Password hasher setup
#pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#def create_test_user():
 #   db: Session = SessionLocal()

  #  existing_user = db.query(User).filter(User.email == "testuser@example.com").first()
   # if existing_user:
    #    print(f"User already exists with ID: {existing_user.id}")
     #   return

   # user = User(
   #     username="testuser",
    #    email="testuser@example.com",
     #   hashed_password=pwd_context.hash("password123")
   # )

  #  db.add(user)
   # db.commit()
   # db.refresh(user)
   # print(f"Test user created with ID: {user.id}")

#if __name__ == "__main__":
 #   create_test_user()
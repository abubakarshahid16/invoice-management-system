from app import app, db, initialize_default_services, User, hash_password


def ensure_seed_data():
    with app.app_context():
        db.create_all()
        initialize_default_services()
        if not User.query.filter_by(username="admin").first():
            admin_user = User(
                username="admin",
                password_hash=hash_password("admin123"),
                email="admin@example.com",
                role="admin",
            )
            db.session.add(admin_user)
            db.session.commit()


if __name__ == "__main__":
    ensure_seed_data()
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

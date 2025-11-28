import os
from datetime import datetime
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Product, Trade, Notification, Message
import uuid

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    category = request.args.get('category', 'all')
    products = []
    
    if current_user.is_authenticated:
        query = Product.query.filter(Product.status == 'active', Product.user_id != current_user.id)
        if category != 'all':
            query = query.filter(Product.category == category)
        products = query.order_by(Product.created_at.desc()).all()
    else:
        # Show 10 random products for non-authenticated users
        query = Product.query.filter(Product.status == 'active')
        if category != 'all':
            query = query.filter(Product.category == category)
        products = query.order_by(db.func.random()).limit(10).all()
    
    return render_template('index.html', products=products, selected_category=category)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        dni = request.form.get('dni')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        department = request.form.get('department')
        city = request.form.get('city')
        photo = request.files.get('photo')

        if password != confirm_password:
            flash('Las contraseñas no coinciden.')
            return redirect(url_for('main.register'))

        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado.')
            return redirect(url_for('main.register'))
        
        if User.query.filter_by(dni=dni).first():
            flash('El DNI ya está registrado.')
            return redirect(url_for('main.register'))

        filename = None
        if photo:
            filename = secure_filename(photo.filename)
            filename = f"{dni}_{filename}"
            photo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

        user = User(name=name, email=email, dni=dni, department=department, city=city, photo=filename, bio='')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registro exitoso. Por favor inicie sesión.')
        return redirect(url_for('main.login'))

    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user is None or not user.check_password(password):
            flash('Email o contraseña inválidos.')
            return redirect(url_for('main.login'))
        
        login_user(user)
        return redirect(url_for('main.index'))
    
    return render_template('login.html')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@bp.route('/user_profile/<int:user_id>')
@login_required
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user_profile.html', user=user)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        email = request.form.get('email')
        bio = request.form.get('bio')
        department = request.form.get('department')
        city = request.form.get('city')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if email != current_user.email:
            if User.query.filter_by(email=email).first():
                flash('El email ya está en uso.')
                return redirect(url_for('main.edit_profile'))
            current_user.email = email
            
        current_user.bio = bio
        current_user.department = department
        current_user.city = city
        
        if password:
            if password != confirm_password:
                flash('Las contraseñas no coinciden.')
                return redirect(url_for('main.edit_profile'))
            current_user.set_password(password)
            
        db.session.commit()
        flash('Perfil actualizado.')
        return redirect(url_for('main.profile'))
        
    return render_template('edit_profile.html')

@bp.route('/publish_object', methods=['GET', 'POST'])
@login_required
def publish_object():
    if request.method == 'POST':
        if current_user.coins < 20:
            flash('No tienes suficientes coins.')
            return redirect(url_for('main.my_objects'))
        
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        condition = request.form.get('condition')
        photos = request.files.getlist('photos')
        
        photo_filenames = []
        for photo in photos:
            if photo:
                filename = secure_filename(photo.filename)
                filename = f"{uuid.uuid4().hex}_{filename}"
                photo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                photo_filenames.append(filename)
        
        product = Product(
            title=title,
            description=description,
            category=category,
            condition=condition,
            photos=",".join(photo_filenames),
            owner=current_user,
            status='active'
        )
        
        current_user.coins -= 20
        db.session.add(product)
        
        # Create notification for publication
        notif = Notification(
            user_id=current_user.id,
            message=f'Has publicado "{title}". Se descontaron 20 coins de tu cuenta.'
        )
        db.session.add(notif)
        db.session.commit()
        
        flash('Objeto publicado exitosamente. Se han descontado 20 coins.')
        return redirect(url_for('main.my_objects'))
        
    return render_template('publish_object.html')

@bp.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template('product_detail.html', product=product)

@bp.route('/my_objects')
@login_required
def my_objects():

    objects = Product.query.filter_by(user_id=current_user.id).filter(Product.status != 'deleted').order_by(Product.created_at.desc()).all()
    return render_template('my_objects.html', objects=objects)

@bp.route('/register_object', methods=['POST'])
@login_required
def register_object():
    title = request.form.get('title')
    description = request.form.get('description')
    category = request.form.get('category')
    condition = request.form.get('condition')
    photos = request.files.getlist('photos')
    
    photo_filenames = []
    for photo in photos:
        if photo:
            filename = secure_filename(photo.filename)
            filename = f"{uuid.uuid4().hex}_{filename}"
            photo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            photo_filenames.append(filename)
    
    product = Product(
        title=title,
        description=description,
        category=category,
        condition=condition,
        photos=",".join(photo_filenames),
        owner=current_user,
        status='draft',
        is_draft=True
    )
    
    db.session.add(product)
    db.session.commit()
    
    flash('Objeto registrado exitosamente. Puedes publicarlo cuando desees.')
    return redirect(url_for('main.my_objects'))

@bp.route('/edit_object/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_object(id):
    product = Product.query.get_or_404(id)
    if product.owner != current_user:
        flash('No tienes permiso.')
        return redirect(url_for('main.my_objects'))
    
    if not product.is_draft:
        flash('Solo puedes editar objetos registrados (no publicados).')
        return redirect(url_for('main.my_objects'))
    
    if request.method == 'POST':
        product.title = request.form.get('title')
        product.description = request.form.get('description')
        product.category = request.form.get('category')
        product.condition = request.form.get('condition')
        
        # Handle new photos if uploaded
        photos = request.files.getlist('photos')
        if photos and photos[0].filename:
            photo_filenames = []
            for photo in photos:
                if photo:
                    filename = secure_filename(photo.filename)
                    filename = f"{uuid.uuid4().hex}_{filename}"
                    photo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    photo_filenames.append(filename)
            product.photos = ",".join(photo_filenames)
        
        db.session.commit()
        flash('Objeto actualizado exitosamente.')
        return redirect(url_for('main.my_objects'))
    
    return render_template('edit_object.html', product=product)

@bp.route('/publish_registered_object/<int:id>', methods=['POST'])
@login_required
def publish_registered_object(id):
    product = Product.query.get_or_404(id)
    if product.owner != current_user:
        flash('No tienes permiso.')
        return redirect(url_for('main.my_objects'))
    
    if not product.is_draft:
        flash('Este objeto ya está publicado.')
        return redirect(url_for('main.my_objects'))
    
    if current_user.coins < 20:
        flash('No tienes suficientes coins para publicar.')
        return redirect(url_for('main.my_objects'))
    
    product.is_draft = False
    product.status = 'active'
    current_user.coins -= 20
    
    # Create notification for publication
    notif = Notification(
        user_id=current_user.id,
        message=f'Has publicado "{product.title}". Se descontaron 20 coins de tu cuenta.'
    )
    db.session.add(notif)
    db.session.commit()
    
    flash('Objeto publicado exitosamente. Se han descontado 20 coins.')
    return redirect(url_for('main.my_objects'))


@bp.route('/withdraw_object/<int:id>', methods=['POST'])
@login_required
def withdraw_object(id):
    product = Product.query.get_or_404(id)
    if product.owner != current_user:
        flash('No tienes permiso.')
        return redirect(url_for('main.my_objects'))
    
    product.status = 'inactive'
    db.session.commit()
    flash('Publicación retirada.')
    return redirect(url_for('main.my_objects'))

@bp.route('/delete_object/<int:id>', methods=['POST'])
@login_required
def delete_object(id):
    product = Product.query.get_or_404(id)
    if product.owner != current_user:
        flash('No tienes permiso.')
        return redirect(url_for('main.my_objects'))
    
    product.status = 'deleted'
    
    # Create notification for deletion
    notif = Notification(
        user_id=current_user.id,
        message=f'Has eliminado la publicación "{product.title}".'
    )
    db.session.add(notif)
    db.session.commit()
    
    flash('Objeto eliminado.')
    return redirect(url_for('main.my_objects'))

@bp.route('/propose_trade/<int:id>', methods=['GET', 'POST'])
@login_required
def propose_trade(id):
    product = Product.query.get_or_404(id)
    if product.owner == current_user:
        flash('No puedes proponer trueque por tu propio objeto.')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        existing_trade = Trade.query.filter_by(proposer_id=current_user.id, product_id=product.id, status='pending').first()
        if existing_trade:
            flash('Ya has propuesto un trueque por este objeto.')
            return redirect(url_for('main.my_trades'))
            
        trade = Trade(proposer_id=current_user.id, receiver_id=product.owner.id, product_id=product.id)
        db.session.add(trade)
        db.session.flush()  # Get trade.id before adding offers
        
        # Get selected offered products (optional)
        offered_product_ids = request.form.getlist('offered_products')
        if offered_product_ids:
            from app.models import TradeOffer
            for product_id in offered_product_ids:
                # Verify product belongs to current user
                offered_product = Product.query.get(int(product_id))
                if offered_product and offered_product.owner == current_user:
                    trade_offer = TradeOffer(trade_id=trade.id, product_id=int(product_id))
                    db.session.add(trade_offer)
        
        notif = Notification(user_id=product.owner.id, message=f"Propuesta de trueque recibida de {current_user.name} por {product.title}")
        db.session.add(notif)
        
        db.session.commit()
        flash('Propuesta enviada.')
        return redirect(url_for('main.my_trades'))
    
    # GET request: get user's registered objects to offer
    my_objects = Product.query.filter_by(user_id=current_user.id).filter(Product.status != 'deleted').all()
    return render_template('propose_trade.html', product=product, my_objects=my_objects)


@bp.route('/my_trades')
@login_required
def my_trades():
    proposed_trades = Trade.query.filter_by(proposer_id=current_user.id).order_by(Trade.created_at.desc()).all()
    received_trades = Trade.query.filter_by(receiver_id=current_user.id).order_by(Trade.created_at.desc()).all()
    return render_template('my_trades.html', proposed_trades=proposed_trades, received_trades=received_trades, now=datetime.utcnow())

@bp.route('/accept_trade/<int:id>', methods=['POST'])
@login_required
def accept_trade(id):
    trade = Trade.query.get_or_404(id)
    if trade.receiver_id != current_user.id:
        flash('No tienes permiso.')
        return redirect(url_for('main.my_trades'))
    
    trade.status = 'accepted'
    
    notif = Notification(user_id=trade.proposer_id, message=f"Tu propuesta por {trade.product.title} ha sido aceptada por {current_user.name}")
    db.session.add(notif)
    
    db.session.commit()
    flash('Trueque aceptado. Ahora ambos deben confirmar.')
    return redirect(url_for('main.my_trades'))

@bp.route('/cancel_trade/<int:id>', methods=['POST'])
@login_required
def cancel_trade(id):
    trade = Trade.query.get_or_404(id)
    if current_user.id not in [trade.proposer_id, trade.receiver_id]:
        flash('No tienes permiso.')
        return redirect(url_for('main.my_trades'))
    
    trade.status = 'cancelled'
    
    other_id = trade.proposer_id if current_user.id == trade.receiver_id else trade.receiver_id
    notif = Notification(user_id=other_id, message=f"El trueque por {trade.product.title} ha sido cancelado por {current_user.name}")
    db.session.add(notif)
    
    db.session.commit()
    flash('Trueque cancelado.')
    return redirect(url_for('main.my_trades'))

@bp.route('/confirm_trade/<int:id>', methods=['POST'])
@login_required
def confirm_trade(id):
    trade = Trade.query.get_or_404(id)
    if current_user.id not in [trade.proposer_id, trade.receiver_id]:
        flash('No tienes permiso.')
        return redirect(url_for('main.my_trades'))
    
    now = datetime.utcnow()
    
    if current_user.id == trade.proposer_id:
        trade.proposer_confirmed_at = now
    else:
        trade.receiver_confirmed_at = now
        
    db.session.commit()
    
    if trade.proposer_confirmed_at and trade.receiver_confirmed_at:
        trade.status = 'completed'
        trade.completed_at = now
        trade.product.status = 'traded'
        
        trade.proposer.coins += 35
        trade.receiver.coins += 35
        
        notif1 = Notification(user_id=trade.proposer_id, message=f"Trueque realizado con éxito! Has ganado 35 coins.")
        notif2 = Notification(user_id=trade.receiver_id, message=f"Trueque realizado con éxito! Has ganado 35 coins.")
        db.session.add(notif1)
        db.session.add(notif2)
        
        db.session.commit()
        flash('¡Trueque completado exitosamente! +35 coins.')
    else:
        flash('Confirmación registrada. Esperando al otro usuario para finalizar.')
        
    return redirect(url_for('main.my_trades'))

@bp.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
    return render_template('notifications.html', notifications=notifs)

@bp.route('/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, read=False).update({'read': True})
    db.session.commit()
    flash('Todas las notificaciones han sido marcadas como leídas.')
    return redirect(url_for('main.notifications'))

@bp.route('/trade/<int:id>/chat', methods=['GET'])
@login_required
def trade_chat(id):
    trade = Trade.query.get_or_404(id)
    
    # Verify user is part of this trade
    if current_user.id not in [trade.proposer_id, trade.receiver_id]:
        flash('No tienes permiso para ver este chat.')
        return redirect(url_for('main.my_trades'))
    
    # Get all messages for this trade
    messages = Message.query.filter_by(trade_id=trade.id).order_by(Message.timestamp.asc()).all()
    
    # Mark messages as read for current user
    for msg in messages:
        if msg.sender_id != current_user.id and not msg.read:
            msg.read = True
    db.session.commit()
    
    # Determine the other user
    other_user = trade.proposer if current_user.id == trade.receiver_id else trade.receiver
    
    return render_template('trade_chat.html', trade=trade, messages=messages, other_user=other_user)

@bp.route('/trade/<int:id>')
@login_required
def trade_details(id):
    trade = Trade.query.get_or_404(id)
    
    # Verify user is part of this trade
    if current_user.id not in [trade.proposer_id, trade.receiver_id]:
        flash('No tienes permiso para ver este trueque.')
        return redirect(url_for('main.my_trades'))
        
    other_user = trade.proposer if current_user.id == trade.receiver_id else trade.receiver
    
    return render_template('trade_details.html', trade=trade, other_user=other_user)


@bp.route('/trade/<int:id>/send_message', methods=['POST'])
@login_required
def send_message(id):
    trade = Trade.query.get_or_404(id)
    
    # Verify user is part of this trade
    if current_user.id not in [trade.proposer_id, trade.receiver_id]:
        flash('No tienes permiso.')
        return redirect(url_for('main.my_trades'))
    
    content = request.form.get('content')
    if content and content.strip():
        message = Message(
            trade_id=trade.id,
            sender_id=current_user.id,
            content=content.strip()
        )
        db.session.add(message)
        db.session.commit()
    
    return redirect(url_for('main.trade_chat', id=trade.id))

@bp.route('/trade/<int:id>/keep_conversation', methods=['POST'])
@login_required
def keep_conversation(id):
    trade = Trade.query.get_or_404(id)
    
    # Verify user is part of this trade
    if current_user.id not in [trade.proposer_id, trade.receiver_id]:
        flash('No tienes permiso.')
        return redirect(url_for('main.my_trades'))
    
    trade.chat_active = True
    db.session.commit()
    flash('Conversación guardada. Puedes retomarla desde "Mis Trueques" > "Chats".')
    return redirect(url_for('main.my_trades'))

@bp.route('/trade/<int:id>/accept_from_chat', methods=['POST'])
@login_required
def accept_from_chat(id):
    trade = Trade.query.get_or_404(id)
    
    # Only receiver can accept
    if trade.receiver_id != current_user.id:
        flash('Solo el propietario del objeto puede aceptar.')
        return redirect(url_for('main.trade_chat', id=trade.id))
    
    if trade.status != 'pending':
        flash('Este trueque ya no está pendiente.')
        return redirect(url_for('main.trade_chat', id=trade.id))
    
    trade.status = 'accepted'
    trade.chat_active = False  # Close chat after accepting
    
    notif = Notification(user_id=trade.proposer_id, message=f"Tu propuesta por {trade.product.title} ha sido aceptada por {current_user.name}")
    db.session.add(notif)
    
    db.session.commit()
    flash('Trueque aceptado. Ahora ambos deben confirmar.')
    return redirect(url_for('main.my_trades'))

@bp.route('/api/trade/<int:id>/messages')
@login_required
def get_messages(id):
    trade = Trade.query.get_or_404(id)
    
    if current_user.id not in [trade.proposer_id, trade.receiver_id]:
        return jsonify({'error': 'Unauthorized'}), 403
        
    messages = Message.query.filter_by(trade_id=trade.id).order_by(Message.timestamp.asc()).all()
    
    # Mark as read
    for msg in messages:
        if msg.sender_id != current_user.id and not msg.read:
            msg.read = True
    db.session.commit()
    
    return jsonify([{
        'id': msg.id,
        'sender_id': msg.sender_id,
        'sender_name': msg.sender.name,
        'content': msg.content,
        'timestamp': msg.timestamp.strftime('%d/%m %H:%M'),
        'is_mine': msg.sender_id == current_user.id
    } for msg in messages])

@bp.route('/api/trade/<int:id>/send', methods=['POST'])
@login_required
def send_message_api(id):
    trade = Trade.query.get_or_404(id)
    
    if current_user.id not in [trade.proposer_id, trade.receiver_id]:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    content = data.get('content')
    
    if content and content.strip():
        message = Message(
            trade_id=trade.id,
            sender_id=current_user.id,
            content=content.strip()
        )
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': {
                'id': message.id,
                'sender_id': message.sender_id,
                'sender_name': message.sender.name,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%d/%m %H:%M'),
                'is_mine': True
            }
        })
    
    return jsonify({'error': 'Empty message'}), 400


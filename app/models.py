from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum


# Enums for various statuses and types
class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    WALLET = "wallet"
    DUITKU_BANK_TRANSFER = "duitku_bank_transfer"
    DUITKU_EWALLET = "duitku_ewallet"
    DUITKU_VIRTUAL_ACCOUNT = "duitku_virtual_account"
    DUITKU_CREDIT_CARD = "duitku_credit_card"


class ProductType(str, Enum):
    VOUCHER = "voucher"
    EXTERNAL_PROVIDER = "external_provider"


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    PURCHASE = "purchase"
    REFUND = "refund"
    WITHDRAWAL = "withdrawal"


class ExternalProviderType(str, Enum):
    DIGIFLAZZ = "digiflazz"
    MANUAL = "manual"


# User model for authentication and profile management
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, max_length=255, regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    username: str = Field(unique=True, max_length=50)
    full_name: str = Field(max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    password_hash: str = Field(max_length=255)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    wallet_balance: Decimal = Field(default=Decimal("0"), decimal_places=2)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    orders: List["Order"] = Relationship(back_populates="user")
    transactions: List["Transaction"] = Relationship(back_populates="user")
    wallet_transactions: List["WalletTransaction"] = Relationship(back_populates="user")


# Game categories and products
class Game(SQLModel, table=True):
    __tablename__ = "games"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    slug: str = Field(max_length=100, unique=True)
    description: str = Field(default="", max_length=1000)
    image_url: Optional[str] = Field(default=None, max_length=500)
    banner_url: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    products: List["Product"] = Relationship(back_populates="game")


class Product(SQLModel, table=True):
    __tablename__ = "products"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="games.id")
    name: str = Field(max_length=200)
    description: str = Field(default="", max_length=1000)
    price: Decimal = Field(decimal_places=2)
    currency: str = Field(default="IDR", max_length=3)
    product_type: ProductType

    # For voucher products
    voucher_code_template: Optional[str] = Field(default=None, max_length=500)

    # For external provider products
    external_provider_type: Optional[ExternalProviderType] = Field(default=None)
    external_product_id: Optional[str] = Field(default=None, max_length=100)
    external_provider_config: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Stock management
    stock_quantity: Optional[int] = Field(default=None)  # None for unlimited
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0)

    # Additional data
    extra_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    game: Game = Relationship(back_populates="products")
    order_items: List["OrderItem"] = Relationship(back_populates="product")
    voucher_codes: List["VoucherCode"] = Relationship(back_populates="product")


# Voucher management for automatic delivery
class VoucherCode(SQLModel, table=True):
    __tablename__ = "voucher_codes"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id")
    code: str = Field(max_length=500)
    serial_number: Optional[str] = Field(default=None, max_length=500)
    is_used: bool = Field(default=False)
    used_at: Optional[datetime] = Field(default=None)
    order_item_id: Optional[int] = Field(default=None, foreign_key="order_items.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    product: Product = Relationship(back_populates="voucher_codes")
    order_item: Optional["OrderItem"] = Relationship(back_populates="voucher_codes")


# Order management system
class Order(SQLModel, table=True):
    __tablename__ = "orders"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    order_number: str = Field(unique=True, max_length=50)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")  # None for guest orders

    # Guest order information
    guest_email: Optional[str] = Field(default=None, max_length=255)
    guest_phone: Optional[str] = Field(default=None, max_length=20)

    # Order details
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    total_amount: Decimal = Field(decimal_places=2)
    currency: str = Field(default="IDR", max_length=3)

    # Game account information
    game_account_id: Optional[str] = Field(default=None, max_length=200)
    game_account_info: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Order processing
    notes: Optional[str] = Field(default=None, max_length=1000)
    admin_notes: Optional[str] = Field(default=None, max_length=1000)
    processed_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: Optional[User] = Relationship(back_populates="orders")
    order_items: List["OrderItem"] = Relationship(back_populates="order")
    payments: List["Payment"] = Relationship(back_populates="order")
    external_orders: List["ExternalProviderOrder"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id")
    product_id: int = Field(foreign_key="products.id")
    quantity: int = Field(default=1)
    unit_price: Decimal = Field(decimal_places=2)
    total_price: Decimal = Field(decimal_places=2)

    # Delivery information
    is_delivered: bool = Field(default=False)
    delivered_at: Optional[datetime] = Field(default=None)
    delivery_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # External provider tracking
    external_reference_id: Optional[str] = Field(default=None, max_length=200)
    external_status: Optional[str] = Field(default=None, max_length=50)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    order: Order = Relationship(back_populates="order_items")
    product: Product = Relationship(back_populates="order_items")
    voucher_codes: List[VoucherCode] = Relationship(back_populates="order_item")


# Payment system
class Payment(SQLModel, table=True):
    __tablename__ = "payments"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id")
    payment_reference: str = Field(unique=True, max_length=100)
    payment_method: PaymentMethod
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    amount: Decimal = Field(decimal_places=2)
    currency: str = Field(default="IDR", max_length=3)

    # Duitku integration
    duitku_merchant_code: Optional[str] = Field(default=None, max_length=20)
    duitku_payment_method: Optional[str] = Field(default=None, max_length=50)
    duitku_reference: Optional[str] = Field(default=None, max_length=100)
    duitku_callback_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Payment URLs
    payment_url: Optional[str] = Field(default=None, max_length=500)
    callback_url: Optional[str] = Field(default=None, max_length=500)
    return_url: Optional[str] = Field(default=None, max_length=500)

    # Timestamps
    expires_at: Optional[datetime] = Field(default=None)
    paid_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    order: Order = Relationship(back_populates="payments")


# Wallet and transaction management
class WalletTransaction(SQLModel, table=True):
    __tablename__ = "wallet_transactions"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    transaction_type: TransactionType
    amount: Decimal = Field(decimal_places=2)
    balance_before: Decimal = Field(decimal_places=2)
    balance_after: Decimal = Field(decimal_places=2)
    reference_id: Optional[str] = Field(default=None, max_length=100)
    reference_type: Optional[str] = Field(default=None, max_length=50)  # 'order', 'payment', 'deposit'
    description: str = Field(max_length=500)
    extra_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="wallet_transactions")


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")  # None for guest transactions
    transaction_reference: str = Field(unique=True, max_length=100)
    transaction_type: TransactionType
    amount: Decimal = Field(decimal_places=2)
    currency: str = Field(default="IDR", max_length=3)
    status: str = Field(max_length=50)

    # References
    order_id: Optional[int] = Field(default=None)
    payment_id: Optional[int] = Field(default=None)

    # Additional data
    description: str = Field(max_length=500)
    extra_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    processed_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: Optional[User] = Relationship(back_populates="transactions")


# External provider integration
class ExternalProvider(SQLModel, table=True):
    __tablename__ = "external_providers"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    provider_type: ExternalProviderType
    is_active: bool = Field(default=True)

    # API configuration
    api_url: str = Field(max_length=500)
    api_key: str = Field(max_length=255)
    api_secret: Optional[str] = Field(default=None, max_length=255)

    # Configuration and settings
    config: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    external_orders: List["ExternalProviderOrder"] = Relationship(back_populates="provider")


class ExternalProviderOrder(SQLModel, table=True):
    __tablename__ = "external_provider_orders"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id")
    provider_id: int = Field(foreign_key="external_providers.id")

    # Provider tracking
    provider_reference_id: str = Field(max_length=200)
    provider_status: str = Field(max_length=50)
    provider_message: Optional[str] = Field(default=None, max_length=1000)

    # Request and response data
    request_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    response_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Timestamps
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    # Relationships
    order: Order = Relationship(back_populates="external_orders")
    provider: ExternalProvider = Relationship(back_populates="external_orders")


# System configuration and settings
class SystemConfig(SQLModel, table=True):
    __tablename__ = "system_configs"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, max_length=100)
    value: str = Field(max_length=1000)
    data_type: str = Field(default="string", max_length=20)  # string, integer, decimal, boolean, json
    description: Optional[str] = Field(default=None, max_length=500)
    is_public: bool = Field(default=False)  # Can be exposed to frontend
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Admin and audit logging
class AdminLog(SQLModel, table=True):
    __tablename__ = "admin_logs"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    admin_user_id: int = Field(foreign_key="users.id")
    action: str = Field(max_length=100)
    resource_type: str = Field(max_length=50)
    resource_id: Optional[int] = Field(default=None)
    old_values: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    new_values: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Non-persistent schemas for validation and API requests/responses


# User schemas
class UserCreate(SQLModel, table=False):
    email: str = Field(max_length=255, regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    username: str = Field(max_length=50)
    full_name: str = Field(max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=255)


class UserUpdate(SQLModel, table=False):
    full_name: Optional[str] = Field(default=None, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)


class UserLogin(SQLModel, table=False):
    email: str = Field(max_length=255)
    password: str = Field(max_length=255)


# Order schemas
class OrderCreate(SQLModel, table=False):
    user_id: Optional[int] = Field(default=None)
    guest_email: Optional[str] = Field(default=None, max_length=255)
    guest_phone: Optional[str] = Field(default=None, max_length=20)
    game_account_id: Optional[str] = Field(default=None, max_length=200)
    game_account_info: Dict[str, Any] = Field(default={})
    notes: Optional[str] = Field(default=None, max_length=1000)


class OrderItemCreate(SQLModel, table=False):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class OrderUpdate(SQLModel, table=False):
    status: Optional[OrderStatus] = Field(default=None)
    admin_notes: Optional[str] = Field(default=None, max_length=1000)


# Product schemas
class ProductCreate(SQLModel, table=False):
    game_id: int
    name: str = Field(max_length=200)
    description: str = Field(default="", max_length=1000)
    price: Decimal = Field(decimal_places=2, ge=0)
    product_type: ProductType
    voucher_code_template: Optional[str] = Field(default=None, max_length=500)
    external_provider_type: Optional[ExternalProviderType] = Field(default=None)
    external_product_id: Optional[str] = Field(default=None, max_length=100)
    stock_quantity: Optional[int] = Field(default=None, ge=0)


class ProductUpdate(SQLModel, table=False):
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    price: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0)
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = Field(default=None)


# Payment schemas
class PaymentCreate(SQLModel, table=False):
    order_id: int
    payment_method: PaymentMethod
    amount: Decimal = Field(decimal_places=2, gt=0)
    return_url: Optional[str] = Field(default=None, max_length=500)


class PaymentCallback(SQLModel, table=False):
    payment_reference: str = Field(max_length=100)
    status: PaymentStatus
    duitku_callback_data: Dict[str, Any] = Field(default={})


# Game schemas
class GameCreate(SQLModel, table=False):
    name: str = Field(max_length=100)
    slug: str = Field(max_length=100)
    description: str = Field(default="", max_length=1000)
    image_url: Optional[str] = Field(default=None, max_length=500)
    banner_url: Optional[str] = Field(default=None, max_length=500)


class GameUpdate(SQLModel, table=False):
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    image_url: Optional[str] = Field(default=None, max_length=500)
    banner_url: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = Field(default=None)


# Wallet schemas
class WalletDeposit(SQLModel, table=False):
    amount: Decimal = Field(decimal_places=2, gt=0)
    payment_method: PaymentMethod


class VoucherCodeCreate(SQLModel, table=False):
    product_id: int
    code: str = Field(max_length=500)
    serial_number: Optional[str] = Field(default=None, max_length=500)


# External provider schemas
class ExternalProviderCreate(SQLModel, table=False):
    name: str = Field(max_length=100)
    provider_type: ExternalProviderType
    api_url: str = Field(max_length=500)
    api_key: str = Field(max_length=255)
    api_secret: Optional[str] = Field(default=None, max_length=255)
    config: Dict[str, Any] = Field(default={})

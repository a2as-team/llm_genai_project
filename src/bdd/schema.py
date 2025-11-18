from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Column, Integer, String, Boolean, Text, Time, Numeric, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class RestaurantTable(Base):
    __tablename__ = "tables"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)  # indoor/outdoor

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    combinable_with: Mapped[list["RestaurantTable"]] = relationship(
        "RestaurantTable",
        secondary="table_combinations",
        primaryjoin="RestaurantTable.id==table_combinations.c.table_id",
        secondaryjoin="RestaurantTable.id==table_combinations.c.combinable_with",
        back_populates="combinable_with",
    )


from sqlalchemy import Table, Column

table_combinations = Table(
    "table_combinations",
    Base.metadata,
    Column("table_id", UUID(as_uuid=True), ForeignKey("tables.id", ondelete="CASCADE"), primary_key=True),
    Column("combinable_with", UUID(as_uuid=True), ForeignKey("tables.id", ondelete="CASCADE"), primary_key=True),
)


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_name: Mapped[str] = mapped_column(String, nullable=False)
    reservation_datetime: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    number_of_guests: Mapped[int] = mapped_column(Integer, nullable=False)
    extra_infos: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tables: Mapped[list["RestaurantTable"]] = relationship(
        secondary="reservation_tables",
        backref="reservations"
    )


reservation_tables = Table(
    "reservation_tables",
    Base.metadata,
    Column("reservation_id", UUID(as_uuid=True), ForeignKey("reservations.id", ondelete="CASCADE"), primary_key=True),
    Column("table_id", UUID(as_uuid=True), ForeignKey("tables.id", ondelete="CASCADE"), primary_key=True),
)


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )


class Formule(Base):
    __tablename__ = "formules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    items: Mapped[list["FormuleItem"]] = relationship(
        "FormuleItem", back_populates="formule", cascade="all, delete-orphan"
    )


class FormuleItem(Base):
    __tablename__ = "formule_items"

    formule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("formules.id", ondelete="CASCADE"),
        primary_key=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("menu_items.id", ondelete="CASCADE"),
        primary_key=True
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    formule: Mapped["Formule"] = relationship("Formule", back_populates="items")
    item: Mapped["MenuItem"] = relationship("MenuItem")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    reservation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reservations.id", ondelete="SET NULL")
    )
    customer_name: Mapped[str | None] = mapped_column(String)
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    reservation: Mapped["Reservation"] = relationship("Reservation")

    formules: Mapped[list["OrderFormule"]] = relationship(
        "OrderFormule",
        back_populates="order",
        cascade="all, delete-orphan"
    )

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )



class OrderFormule(Base):
    __tablename__ = "order_formules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE")
    )

    formule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("formules.id"),
        nullable=True
    )

    formule_name: Mapped[str] = mapped_column(String, nullable=False)
    formula_base_price: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    order: Mapped["Order"] = relationship("Order", back_populates="formules")
    formule: Mapped["Formule"] = relationship("Formule")

    items: Mapped[list["OrderFormuleItem"]] = relationship(
        "OrderFormuleItem",
        back_populates="order_formule",
        cascade="all, delete-orphan"
    )

class OrderFormuleItem(Base):
    __tablename__ = "order_formule_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    order_formule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("order_formules.id", ondelete="CASCADE")
    )

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("menu_items.id")
    )

    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    indications: Mapped[str | None] = mapped_column(Text)

    order_formule: Mapped["OrderFormule"] = relationship("OrderFormule", back_populates="items")
    item: Mapped["MenuItem"] = relationship("MenuItem")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE")
    )

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("menu_items.id")
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    indications: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    item: Mapped["MenuItem"] = relationship("MenuItem")

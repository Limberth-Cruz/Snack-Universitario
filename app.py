from flask import Flask, render_template, request, redirect, url_for, flash
from conexion import conectar

app = Flask(__name__)
app.secret_key = "snack_universitario"


# ---------------------------------------
# PÁGINA PRINCIPAL - VENTAS
# ---------------------------------------
@app.route("/")
def ventas():

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT id_producto, nombre, precio, stock
        FROM productos
        WHERE stock > 0
        ORDER BY nombre
    """)

    productos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template("ventas.html", productos=productos)


# ---------------------------------------
# REGISTRAR VENTA
# ---------------------------------------
@app.route("/registrar_venta", methods=["POST"])
def registrar_venta():

    productos_ids = request.form.getlist("id_producto")
    cantidades = request.form.getlist("cantidad")
    metodo_pago = request.form.get("metodo_pago")

    if not productos_ids:
        flash("No hay productos en la venta.")
        return redirect(url_for("ventas"))

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    try:

        total = 0
        detalles = []

        # --------------------------------
        # VERIFICAR PRODUCTOS Y STOCK
        # --------------------------------
        for i in range(len(productos_ids)):

            id_producto = int(productos_ids[i])
            cantidad = int(cantidades[i])

            if cantidad <= 0:
                continue

            cursor.execute("""
                SELECT id_producto, nombre, precio, stock
                FROM productos
                WHERE id_producto = %s
            """, (id_producto,))

            producto = cursor.fetchone()

            if not producto:
                raise Exception("Producto no encontrado.")

            if producto["stock"] < cantidad:
                raise Exception(
                    f"No hay suficiente stock de {producto['nombre']}."
                )

            subtotal = float(producto["precio"]) * cantidad

            total += subtotal

            detalles.append({
                "id_producto": id_producto,
                "cantidad": cantidad,
                "precio": producto["precio"],
                "subtotal": subtotal
            })

        if not detalles:
            raise Exception("Debe seleccionar al menos un producto.")

        # --------------------------------
        # GUARDAR VENTA
        # --------------------------------
        cursor.execute("""
            INSERT INTO ventas (total, metodo_pago)
            VALUES (%s, %s)
        """, (total, metodo_pago))

        id_venta = cursor.lastrowid

        # --------------------------------
        # GUARDAR DETALLES Y ACTUALIZAR STOCK
        # --------------------------------
        for detalle in detalles:

            cursor.execute("""
                INSERT INTO detalle_ventas
                (
                    id_venta,
                    id_producto,
                    cantidad,
                    precio_unitario,
                    subtotal
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                id_venta,
                detalle["id_producto"],
                detalle["cantidad"],
                detalle["precio"],
                detalle["subtotal"]
            ))

            cursor.execute("""
                UPDATE productos
                SET stock = stock - %s
                WHERE id_producto = %s
            """, (
                detalle["cantidad"],
                detalle["id_producto"]
            ))

        conexion.commit()

        flash(
            f"Venta registrada correctamente. "
            f"Total: Bs. {total:.2f}"
        )

    except Exception as e:

        conexion.rollback()
        flash(f"Error: {e}")

    finally:

        cursor.close()
        conexion.close()

    return redirect(url_for("ventas"))


# ---------------------------------------
# HISTORIAL DE VENTAS
# ---------------------------------------
@app.route("/historial")
def historial():

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id_venta,
            fecha,
            total,
            metodo_pago
        FROM ventas
        ORDER BY fecha DESC
    """)

    ventas = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "historial.html",
        ventas=ventas
    )

@app.route("/productos", methods=["GET", "POST"])
def productos():

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    if request.method == "POST":

        nombre = request.form.get("nombre")
        precio = request.form.get("precio")
        stock = request.form.get("stock")

        if not nombre or not precio or not stock:
            flash("Todos los campos son obligatorios.")

        else:
            try:

                cursor.execute("""
                    INSERT INTO productos
                    (nombre, precio, stock)
                    VALUES (%s, %s, %s)
                """, (
                    nombre,
                    float(precio),
                    int(stock)
                ))

                conexion.commit()

                flash("Producto agregado correctamente.")

            except Exception as e:

                conexion.rollback()
                flash(f"Error: {e}")

    cursor.execute("""
        SELECT id_producto, nombre, precio, stock
        FROM productos
        ORDER BY nombre
    """)

    lista_productos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "productos.html",
        productos=lista_productos
    )
# ---------------------------------------
# EJECUTAR SERVIDOR
# ---------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
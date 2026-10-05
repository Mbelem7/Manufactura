document.addEventListener("DOMContentLoaded", () => {
    const addButton = document.getElementById("addSaleItemButton");
    const tableBody = document.getElementById("saleItemsTableBody");

    if (!addButton || !tableBody) {
        return;
    }

    const createRow = () => {
        const row = document.createElement("tr");

        row.classList.add("sale-item-row");

        row.innerHTML = `
            <td>
                <select
                    name="producto_id[]"
                    class="form-select"
                    required
                >
                    <option value="">
                        Seleccione un producto
                    </option>
                </select>
            </td>

            <td>
                <input
                    type="number"
                    name="cantidad[]"
                    class="form-control"
                    min="0.01"
                    step="0.01"
                    placeholder="0.00"
                    required
                >
            </td>

            <td>
                <div class="input-group">

                    <span class="input-group-text">
                        C$
                    </span>

                    <input
                        type="number"
                        name="precio_unitario[]"
                        class="form-control"
                        min="0"
                        step="0.01"
                        placeholder="0.00"
                        required
                    >

                </div>
            </td>

            <td class="text-end">

                <button
                    type="button"
                    class="btn btn-outline-danger btn-sm remove-sale-item"
                    title="Eliminar producto"
                >
                    <i class="bi bi-trash"></i>
                </button>

            </td>
        `;

        return row;
    };


    addButton.addEventListener("click", () => {
        tableBody.appendChild(createRow());
    });


    tableBody.addEventListener("click", (event) => {
        const removeButton = event.target.closest(".remove-sale-item");

        if (!removeButton) {
            return;
        }

        const rows = tableBody.querySelectorAll(".sale-item-row");

        if (rows.length <= 1) {
            return;
        }

        removeButton.closest(".sale-item-row").remove();
    });
});
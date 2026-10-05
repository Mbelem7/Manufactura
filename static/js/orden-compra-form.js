document.addEventListener("DOMContentLoaded", () => {
    const addButton = document.getElementById("addPurchaseItemButton");
    const tableBody = document.getElementById("purchaseItemsTableBody");

    if (!addButton || !tableBody) {
        return;
    }

    const createRow = () => {
        const row = document.createElement("tr");

        row.classList.add("purchase-item-row");

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
                        name="costo_unitario[]"
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
                    class="btn btn-outline-danger btn-sm remove-purchase-item"
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
        const removeButton = event.target.closest(".remove-purchase-item");

        if (!removeButton) {
            return;
        }

        const rows = tableBody.querySelectorAll(".purchase-item-row");

        if (rows.length <= 1) {
            return;
        }

        removeButton.closest(".purchase-item-row").remove();
    });
});
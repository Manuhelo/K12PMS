document.addEventListener('DOMContentLoaded', function () {
    const poSelect = document.querySelector('#id_purchase_order');

    if (poSelect) {
        poSelect.addEventListener('change', function () {
            const poId = this.value;
            if (!poId) return;

            fetch(`/inventory/ajax/get-po-products/?po_id=${poId}`)
                .then(response => response.json())
                .then(data => {
                    const selects = document.querySelectorAll('select[id$="product"]');
                    selects.forEach(select => {
                        // Clear existing options
                        select.innerHTML = '';
                        // Add new options
                        data.forEach(item => {
                            const option = document.createElement('option');
                            option.value = item.id;
                            option.text = item.name;
                            select.appendChild(option);
                        });
                    });
                });
        });
    }
});

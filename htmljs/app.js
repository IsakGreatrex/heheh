document.addEventListener('DOMContentLoaded', function() {
    const canvas = new fabric.Canvas('nft-canvas');
    let baseImage = null;

    // Handle image upload for the canvas
    document.getElementById('imageUploader').addEventListener('change', function(e) {
        const reader = new FileReader();
        reader.onload = function(event) {
            const imgObj = new Image();
            imgObj.src = event.target.result;
            imgObj.onload = function() {
                const img = new fabric.Image(imgObj);

                // Set canvas size to match the uploaded image size
                canvas.setWidth(img.width);
                canvas.setHeight(img.height);

                img.set({
                    left: 0,
                    top: 0,
                    originX: 'left',
                    originY: 'top',
                    selectable: false, // Make the image unselectable
                    evented: false,    // Make the image unresponsive to events
                });

                canvas.clear(); // Clear existing content
                canvas.add(img);
                canvas.renderAll();
                baseImage = img;
            };
        };
        reader.readAsDataURL(e.target.files[0]);
    });

    // Handle sticker upload
    document.getElementById('stickerUploader').addEventListener('change', function(e) {
        const reader = new FileReader();
        reader.onload = function(event) {
            const stickerImg = new Image();
            stickerImg.src = event.target.result;
            stickerImg.onload = function() {
                const stickerElement = document.createElement('img');
                stickerElement.src = stickerImg.src;
                stickerElement.className = 'sticker';
                stickerElement.draggable = true;
                document.getElementById('sticker-panel').appendChild(stickerElement);

                // Add dragstart event to the newly added sticker
                stickerElement.addEventListener('dragstart', function(e) {
                    e.dataTransfer.setData('text', this.src);
                    e.dataTransfer.setData('stickerSize', Math.min(canvas.width, canvas.height) * 0.25);
                });
            };
        };
        reader.readAsDataURL(e.target.files[0]);
    });

    // Initialize stickers in the panel to be draggable
    document.querySelectorAll('.sticker').forEach(sticker => {
        sticker.addEventListener('dragstart', function(e) {
            e.dataTransfer.setData('text', this.src);
            e.dataTransfer.setData('stickerSize', Math.min(canvas.width, canvas.height) * 0.25);
        });
    });

    // Handle drag and drop for stickers
    canvas.wrapperEl.addEventListener('dragover', function(e) {
        e.preventDefault(); // Necessary to allow drop
    });

    canvas.wrapperEl.addEventListener('drop', function(e) {
        e.preventDefault();
        const src = e.dataTransfer.getData('text');
        const stickerSize = parseFloat(e.dataTransfer.getData('stickerSize'));
        const pointer = canvas.getPointer(e);

        fabric.Image.fromURL(src, function(img) {
            const scale = stickerSize / img.width;
            img.set({
                left: pointer.x,
                top: pointer.y,
                scaleX: scale,
                scaleY: scale,
                originX: 'center',
                originY: 'center',
                borderColor: 'white',
                cornerColor: 'black',
                cornerSize: 6,
                transparentCorners: false,
            });
            canvas.add(img);
            canvas.setActiveObject(img);
            canvas.renderAll();
        });
    });

    // Handle Save button click
    document.getElementById('saveButton').addEventListener('click', function() {
        const dataURL = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.href = dataURL;
        link.download = 'heheh.png';
        link.click();
    });

    // Handle Add Text button click
    document.getElementById('addTextButton').addEventListener('click', function() {
        const topText = prompt("Enter top text:");
        const bottomText = prompt("Enter bottom text:");

        if (topText) {
            const topTextObj = new fabric.Text(topText, {
                left: canvas.getWidth() / 2,
                top: 20,
                fontFamily: 'Impact',
                fontSize: 40,
                fill: '#fff',
                stroke: '#000',
                strokeWidth: 2,
                originX: 'center',
                originY: 'top',
                textAlign: 'center',
            });
            canvas.add(topTextObj);
        }

        if (bottomText) {
            const bottomTextObj = new fabric.Text(bottomText, {
                left: canvas.getWidth() / 2,
                top: canvas.getHeight() - 40,
                fontFamily: 'Impact',
                fontSize: 40,
                fill: '#fff',
                stroke: '#000',
                strokeWidth: 2,
                originX: 'center',
                originY: 'bottom',
                textAlign: 'center',
            });
            canvas.add(bottomTextObj);
        }

        canvas.renderAll();
    });
});

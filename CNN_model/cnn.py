import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping

#Pre processing the dataset, including slight data augmentation but no drastic changes
train_datagen = ImageDataGenerator(
    rescale = 1./255,
    rotation_range=10, #Small tilts
    width_shift_range=0.1, #Small horizontal camera shifts
    height_shift_range=0.05, #Small vertical tilts
    brightness_range=[0.7, 1.3], #Simulation of different lighting conditions
    horizontal_flip = False, #Disable flips
    validation_split=0.2 #Split 20% of training set for validation
)

training_set = train_datagen.flow_from_directory(
    '../data_collection/dataset/images/train',
    target_size = (64, 64),
    batch_size = 16,
    class_mode = 'categorical',
    subset='training'
)

validation_set = train_datagen.flow_from_directory(
    '../data_collection/dataset/images/train',
    target_size = (64, 64),
    batch_size = 16,
    class_mode = 'categorical',
    subset='validation'
)

#Preprocessing test set
test_datagen = ImageDataGenerator(rescale = 1./255)
test_set = test_datagen.flow_from_directory(
    '../data_collection/dataset/images/test',
    target_size = (64, 64),
    batch_size = 32,
    class_mode = 'categorical',
    shuffle=False
)

#Initialize the CNN
cnn = tf.keras.models.Sequential()

#Convolution
cnn.add(tf.keras.layers.Conv2D(filters=32, kernel_size=3, activation='relu', input_shape=[64, 64, 3]))

#Pooling
cnn.add(tf.keras.layers.MaxPool2D(pool_size=2, strides=2))

#Second convolutional layer
cnn.add(tf.keras.layers.Conv2D(filters=32, kernel_size=3, activation='relu'))

cnn.add(tf.keras.layers.MaxPool2D(pool_size=2, strides=2))

#Flattening
cnn.add(tf.keras.layers.Flatten())

#Full connection
cnn.add(tf.keras.layers.Dense(units=128, activation='relu'))

#Output layer
cnn.add(tf.keras.layers.Dense(units=3, activation='softmax'))

#Compiling the CNN
cnn.compile(optimizer = 'adam', loss = 'categorical_crossentropy', metrics = ['accuracy'])

#Early stopping to avoid overfitting
early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

#Training and testing the CNN on the dataset
cnn.fit(x = training_set, validation_data = validation_set, epochs = 25, callbacks=[early_stop])

#Evaluate on test set
loss, accuracy = cnn.evaluate(test_set)
print(f"Test Accuracy: {accuracy*100:.2f}%")

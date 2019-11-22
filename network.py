from tensorflow.keras.applications.vgg19 import VGG19

import tensorflow.keras.backend as K
import tensorflow.keras.layers as layers
import tensorflow.keras.models as models

class Encoder(models.Model):
  def __init__(self, name='encoder', encoder_layers=['block1_conv1', 'block2_conv1', 'block3_conv1', 'block4_conv1'], input_shape=(None, None, 3), **kwargs):
    assert len(encoder_layers) > 0, 'No "encoder_layers" is provided.'
    
    super(Encoder, self).__init__(name=name, **kwargs)
    vgg = VGG19(input_tensor=layers.Input(shape=input_shape))
    output_layers = [vgg.get_layer(layer_name).output for layer_name in encoder_layers]
    self.encoder = models.Model(inputs=vgg.input, outputs=output_layers)

  def call(self, x):
    return self.encoder(x)

class ReflectionPad(layers.Layer):
  def __init__(self, padding, name='reflection', *args, **kwargs):
    super(ReflectionPad, self).__init__(name=name, **kwargs)
    self.pad_left, self.pad_right, self.pad_top, self.pad_bottom = padding

  def compute_output_shape(self, input_shape):
    return (input_shape[0], input_shape[1] + self.pad_left + self.pad_right, input_shape[2], self.pad_top, self.pad_bottom, input_shape[3])

  def call(self, x):
    x = K.concatenate([K.reverse(x, 1)[:, (-1 - self.pad_left):-1, :, :], x, K.reverse(x, 1)[:, 1:(1 + self.pad_right), :, :]], axis=1)
    x = K.concatenate([K.reverse(x, 2)[:, :, (-1 - self.pad_top):-1, :], x, K.reverse(x, 2)[:, :, 1:(1 + self.pad_bottom), :]], axis=2)
    return x

class Decoder(models.Model):
  def __init__(self, name='decoder', **kwargs):
    super(Decoder, self).__init__(name=name, **kwargs)
    self.decoder = models.Sequential([
      ReflectionPad((1, 1, 1, 1)),
      layers.Conv2D(),
      layers.Upsample(size=2, interpolation='nearest'),
      ReflectionPad((1, 1, 1, 1)),
      layers.Conv2D(),
      ReflectionPad((1, 1, 1, 1)),
      layers.Conv2D(),
      ReflectionPad((1, 1, 1, 1)),
      layers.Conv2D(),
      ReflectionPad((1, 1, 1, 1)),
      layers.Conv2D(),
      layers.Upsample(size=2, interpolation='nearest'),
      ReflectionPad((1, 1, 1, 1)),
      layers.Conv2D(),
      ReflectionPad((1, 1, 1, 1)),
      layers.Conv2D(),
      layers.Upsample(size=2, interpolation='nearest'),
      ReflectionPad((1, 1, 1, 1)),
      layers.Conv2D(),
      ReflectionPad((1, 1, 1, 1)),
      layers.Conv2D()
    ])

  def call(self, x):
    return self.decoder(x)

class AdaIN(layers.Layer):
  def __init__(self, name='adain', alpha=1.0, **kwargs):
    super(AdaIN, self).__init__(name=name, **kwargs)
    self.alpha = alpha

  def compute_output_shape(self, input_shape):
    return input_shape[0]

  def call(self, x):
    content_features, style_features = x
    content_mean = K.mean(content_features, axis=[1, 2], keepdim=True)
    content_var = K.variance(content_features, axis=[1, 2], keepdim=True)
    style_mean = K.mean(style_features, axis=[1, 2], keepdim=True)
    style_var = K.variance(style_features, axis=[1, 2], keepdim=True)
    normalized_content_features = K.batch_normalization(content_features, content_mean, content_var, style_mean, K.sqrt(style_var), epsilon=1e-5)
    return self.alpha * normalized_content_features + (1 - self.alpha) * content_features
    
class Stylizer(models.Model):
  def __init__(self, name='stylizer', **kwargs):
    super(Stylizer, self).__init__(name=name, **kwargs)

  def call(self):
    raise NotImplemented

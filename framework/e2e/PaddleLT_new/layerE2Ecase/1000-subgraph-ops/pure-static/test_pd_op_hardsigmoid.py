import os
if os.getenv('FLAGS_cinn_new_group_scheduler') is None:
    os.environ['FLAGS_cinn_new_group_scheduler'] = '1'
if os.getenv('FLAGS_group_schedule_tiling_first') is None:
    os.environ['FLAGS_group_schedule_tiling_first'] = '1'
if os.getenv('FLAGS_prim_all') is None:
    os.environ['FLAGS_prim_all'] = 'true'
if os.getenv('FLAGS_prim_enable_dynamic') is None:
    os.environ['FLAGS_prim_enable_dynamic'] = '1'
if os.getenv('FLAGS_enable_pir_api') is None:
    os.environ['FLAGS_enable_pir_api'] = '1'
if os.getenv('FLAGS_cinn_bucket_compile') is None:
    os.environ['FLAGS_cinn_bucket_compile'] = '1'

import unittest
import numpy as np
import paddle

def GetEnvVarEnableJit():
    enable_jit = os.getenv('PADDLE_DEBUG_ENABLE_JIT')
    return enable_jit not in {
        "0",
        "False",
        "false",
        "OFF",
    }

def GetEnvVarEnableCinn():
    enable_cinn = os.getenv('PADDLE_DEBUG_ENABLE_CINN')
    if enable_cinn is None:
        return True
    return enable_cinn not in {
        "0",
        "False",
        "false",
        "OFF",
    }


def GetTolerance(dtype):
    if dtype == np.float16:
        return GetFloat16Tolerance()
    if dtype == np.float32:
        return GetFloat32Tolerance()
    return 1e-6

def GetFloat16Tolerance():
    try:
        return float(os.getenv('PADDLE_DEBUG_FLOAT16_TOL'))
    except:
        return 1e-3

def GetFloat32Tolerance():
    try:
        return float(os.getenv('PADDLE_DEBUG_FLOAT32_TOL'))
    except:
        return 1e-6

def IsInteger(dtype):
    return np.dtype(dtype).char in np.typecodes['AllInteger']

def ApplyToStatic(net, use_cinn):
    build_strategy = paddle.static.BuildStrategy()
    build_strategy.build_cinn_pass = use_cinn
    return paddle.jit.to_static(
        net,
        input_spec=net.get_input_spec(),
        build_strategy=build_strategy,
        full_graph=True,
    )

class InstanceTrait:

    @classmethod
    def instance(cls):
        if cls.instance_ is None:
            cls.instance_ = cls()
        return cls.instance_

    @classmethod
    def static_instance_with_cinn(cls):
        if cls.static_instance_with_cinn_ is None:
            cls.static_instance_with_cinn_ = ApplyToStatic(
                cls.instance(),
                use_cinn=True
            )
        return cls.static_instance_with_cinn_

    @classmethod
    def static_instance_without_cinn(cls):
        if cls.static_instance_without_cinn_ is None:
            cls.static_instance_without_cinn_ = ApplyToStatic(
                cls.instance(),
                use_cinn=False
            )
        return cls.static_instance_without_cinn_


class CinnTestBase:

    def setUp(self):
        paddle.seed(2024)
        self.prepare_data()

    def test_train(self):
        dy_outs = self.train(use_cinn=False)
        cinn_outs = self.train(use_cinn=GetEnvVarEnableCinn())

        for cinn_out, dy_out in zip(cinn_outs, dy_outs):
          if type(cinn_out) is list and type(dy_out) is list:
            for x, y in zip(cinn_out, dy_out):
              self.assert_all_close(x, y)
          else:
            self.assert_all_close(cinn_out, dy_out)

    def train(self, use_cinn):
        if GetEnvVarEnableJit():
            net = self.prepare_static_net(use_cinn)
        else:
            net = self.prepare_net()
        out = net(*self.inputs)
        return out
    
    def prepare_data(self):
        self.inputs = self.get_inputs()
        for input in self.inputs:
            input.stop_gradient = True

    def prepare_net(self):
        return self.get_test_class().instance()

    def prepare_static_net(self, use_cinn):
        if use_cinn:
            return self.get_test_class().static_instance_with_cinn()
        else:
            return self.get_test_class().static_instance_without_cinn()

    def assert_all_close(self, x, y):
        if (hasattr(x, "numpy") and hasattr(y, "numpy")):
            x_numpy = x.numpy()
            y_numpy = y.numpy()
            assert x_numpy.dtype == y_numpy.dtype
            if IsInteger(x_numpy.dtype):
                np.testing.assert_equal(x_numpy, y_numpy)
            else:
                tol = GetTolerance(x_numpy.dtype)
                np.testing.assert_allclose(x_numpy, y_numpy, atol=tol, rtol=tol)
        else:
            assert x == y



class PrimitiveOp_f79edaa32ac6c3071c3fd00dce083d79(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 480, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_29eea5cc5f8ac1441add15c9ae7c042f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_f79edaa32ac6c3071c3fd00dce083d79
    def get_inputs(self):
        return [
            paddle.uniform([1, 480, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_84793998d56a5b43308d58069fd7187d(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.2, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 576, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_58fad75e452dee2cc5c594046d460648(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_84793998d56a5b43308d58069fd7187d
    def get_inputs(self):
        return [
            paddle.uniform([1, 576, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_331e94bee2bd309814f937015f72199a(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 48, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_21f695c7bac04e3be9dcf20b1bbb6af3(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_331e94bee2bd309814f937015f72199a
    def get_inputs(self):
        return [
            paddle.uniform([1, 48, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_5e2ab8415cdd5e6e19c4c55b98d4b1b7(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 160, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_c17a3f4a55ad6e95a6f4ee66e017e71d(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_5e2ab8415cdd5e6e19c4c55b98d4b1b7
    def get_inputs(self):
        return [
            paddle.uniform([1, 160, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_64b3612fb370de353a1b268c3b821236(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 768, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_173a788c7dcc2e2fae557fbff395174a(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_64b3612fb370de353a1b268c3b821236
    def get_inputs(self):
        return [
            paddle.uniform([1, 768, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_c5ada77aea41c1b14fb8d9e874274ab8(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.2, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 672, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_4cdd16c01bd63b0b75610cf0280e129f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c5ada77aea41c1b14fb8d9e874274ab8
    def get_inputs(self):
        return [
            paddle.uniform([1, 672, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_0d01762121dbb8c04d505ae04a4ae0a3(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.2, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 120, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_f9f0092946410c5b46b82831d1f41c74(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_0d01762121dbb8c04d505ae04a4ae0a3
    def get_inputs(self):
        return [
            paddle.uniform([1, 120, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_87526143ba591b5e347947beca130c76(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 72, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_4ea1b1f9f24b2cd69b4b3f5ae2922ddc(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_87526143ba591b5e347947beca130c76
    def get_inputs(self):
        return [
            paddle.uniform([1, 72, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_e181865e0ba9f8a0e82bd65bd8272122(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 120, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_daa3c17d2bdad7e3ef413762a3195594(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e181865e0ba9f8a0e82bd65bd8272122
    def get_inputs(self):
        return [
            paddle.uniform([1, 120, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_ac586694e388164438a8f3fe885eece7(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 384, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_76186274a8f7c7d0e7d5c3152ccec758(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ac586694e388164438a8f3fe885eece7
    def get_inputs(self):
        return [
            paddle.uniform([1, 384, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_74a9c3274e82fd70e05b97a97c64f676(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.2, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 960, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_de1046a18a5f5319903d1e2b075a1ee2(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_74a9c3274e82fd70e05b97a97c64f676
    def get_inputs(self):
        return [
            paddle.uniform([1, 960, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_c2ffdc91577917ee4518ce373991df84(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.2, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 96, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_6c710e32bdedbea78331a048c69e2c54(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c2ffdc91577917ee4518ce373991df84
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_e6a06100d93af8c10246d4d9b29f0be6(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.2, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 72, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_d67683acc6e169e88087ec5fa7b63001(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e6a06100d93af8c10246d4d9b29f0be6
    def get_inputs(self):
        return [
            paddle.uniform([1, 72, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_de1046a18a5f5319903d1e2b075a1ee2(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_74a9c3274e82fd70e05b97a97c64f676
    def get_inputs(self):
        return [
            paddle.uniform([1, 960, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_e2a1c1a79597dfe808eaa0d0049ddaa9(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 192, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_9f00f04fb884c3d958e4e70992be8bfb(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e2a1c1a79597dfe808eaa0d0049ddaa9
    def get_inputs(self):
        return [
            paddle.uniform([1, 192, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_76186274a8f7c7d0e7d5c3152ccec758(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ac586694e388164438a8f3fe885eece7
    def get_inputs(self):
        return [
            paddle.uniform([1, 384, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_8c177c5e1c474f3174532ce773e1de32(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 96, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_bc505fdcaf85a2fe10f0aa1f464cf90e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c177c5e1c474f3174532ce773e1de32
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_bc505fdcaf85a2fe10f0aa1f464cf90e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c177c5e1c474f3174532ce773e1de32
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_9f00f04fb884c3d958e4e70992be8bfb(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e2a1c1a79597dfe808eaa0d0049ddaa9
    def get_inputs(self):
        return [
            paddle.uniform([1, 192, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_9f00f04fb884c3d958e4e70992be8bfb(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e2a1c1a79597dfe808eaa0d0049ddaa9
    def get_inputs(self):
        return [
            paddle.uniform([1, 192, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_6e935281a74f84740567baf06dd39234(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.2, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 16, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_930f9ceff0769f934e605abbbba053b2(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_6e935281a74f84740567baf06dd39234
    def get_inputs(self):
        return [
            paddle.to_tensor([[[[1.4773393869400024]], [[1.5512890815734863]], [[1.5321698188781738]], [[1.8476449251174927]], [[1.3322175741195679]], [[0.9880713224411011]], [[1.7650210857391357]], [[1.9648226499557495]], [[1.2823586463928223]], [[1.8251773118972778]], [[1.6506630182266235]], [[1.137101173400879]], [[1.6821203231811523]], [[1.6746923923492432]], [[1.708193302154541]], [[0.7750889658927917]]]], dtype='float32').reshape([1, 16, 1, 1]),
        ]


class TestPrimitiveOp_9f00f04fb884c3d958e4e70992be8bfb(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e2a1c1a79597dfe808eaa0d0049ddaa9
    def get_inputs(self):
        return [
            paddle.uniform([1, 192, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_6c53ad76abc8e8d50f55fee93f7fb47c(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 44, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_18e88055cf1f13d94f9bb7715e16ac44(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_6c53ad76abc8e8d50f55fee93f7fb47c
    def get_inputs(self):
        return [
            paddle.uniform([1, 44, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_c17a3f4a55ad6e95a6f4ee66e017e71d(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_5e2ab8415cdd5e6e19c4c55b98d4b1b7
    def get_inputs(self):
        return [
            paddle.uniform([1, 160, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_de1046a18a5f5319903d1e2b075a1ee2(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_74a9c3274e82fd70e05b97a97c64f676
    def get_inputs(self):
        return [
            paddle.uniform([1, 960, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_29eea5cc5f8ac1441add15c9ae7c042f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_f79edaa32ac6c3071c3fd00dce083d79
    def get_inputs(self):
        return [
            paddle.uniform([1, 480, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_f9f0092946410c5b46b82831d1f41c74(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_0d01762121dbb8c04d505ae04a4ae0a3
    def get_inputs(self):
        return [
            paddle.uniform([1, 120, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4cdd16c01bd63b0b75610cf0280e129f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c5ada77aea41c1b14fb8d9e874274ab8
    def get_inputs(self):
        return [
            paddle.uniform([1, 672, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_e98a6057ab8ac29e7554ebf80879f084(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 64, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_ab77adfa52800ffaedacc5af48e4900f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e98a6057ab8ac29e7554ebf80879f084
    def get_inputs(self):
        return [
            paddle.uniform([1, 64, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4cdd16c01bd63b0b75610cf0280e129f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c5ada77aea41c1b14fb8d9e874274ab8
    def get_inputs(self):
        return [
            paddle.uniform([1, 672, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_0b02b820ca3845b450ccc06fc185d037(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 128, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_3244ea5ab118ad2b2c431328f2879520(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_0b02b820ca3845b450ccc06fc185d037
    def get_inputs(self):
        return [
            paddle.uniform([1, 128, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_29eea5cc5f8ac1441add15c9ae7c042f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_f79edaa32ac6c3071c3fd00dce083d79
    def get_inputs(self):
        return [
            paddle.uniform([1, 480, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_daa3c17d2bdad7e3ef413762a3195594(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e181865e0ba9f8a0e82bd65bd8272122
    def get_inputs(self):
        return [
            paddle.uniform([1, 120, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_f13ffc13df02b96e0c965046751b95cf(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 320, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_132a9c56c5542f70b08b59da10d84f9c(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_f13ffc13df02b96e0c965046751b95cf
    def get_inputs(self):
        return [
            paddle.uniform([1, 320, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_ef4004d2bfd110446d0cd9fc2342a3ba(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 100, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_8a1e5809c8e2ff4f705bc947bd646a11(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ef4004d2bfd110446d0cd9fc2342a3ba
    def get_inputs(self):
        return [
            paddle.uniform([1, 100, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_de1046a18a5f5319903d1e2b075a1ee2(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_74a9c3274e82fd70e05b97a97c64f676
    def get_inputs(self):
        return [
            paddle.uniform([1, 960, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4cdd16c01bd63b0b75610cf0280e129f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c5ada77aea41c1b14fb8d9e874274ab8
    def get_inputs(self):
        return [
            paddle.uniform([1, 672, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_ec9d38a776abf5ba1e4f243247f6880a(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 256, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_873fef0881c4350ef309136433df873a(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ec9d38a776abf5ba1e4f243247f6880a
    def get_inputs(self):
        return [
            paddle.uniform([1, 256, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_76186274a8f7c7d0e7d5c3152ccec758(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ac586694e388164438a8f3fe885eece7
    def get_inputs(self):
        return [
            paddle.uniform([1, 384, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_e8e48567d534d700c51eb2a8fb93f95d(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 240, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_6d034535ffb2022244834dfbb95b59ad(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e8e48567d534d700c51eb2a8fb93f95d
    def get_inputs(self):
        return [
            paddle.uniform([1, 240, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_1ca16c2429fb25bce935f97b484db58f(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 80, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_c2b45a2bfdae3d6d6790aafbac992415(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_1ca16c2429fb25bce935f97b484db58f
    def get_inputs(self):
        return [
            paddle.uniform([1, 80, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4cdd16c01bd63b0b75610cf0280e129f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c5ada77aea41c1b14fb8d9e874274ab8
    def get_inputs(self):
        return [
            paddle.uniform([1, 672, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_132a9c56c5542f70b08b59da10d84f9c(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_f13ffc13df02b96e0c965046751b95cf
    def get_inputs(self):
        return [
            paddle.uniform([1, 320, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_bc505fdcaf85a2fe10f0aa1f464cf90e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c177c5e1c474f3174532ce773e1de32
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_6e768ecbca6e75bbe2c933dabcadaee2(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.2, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 480, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_92aa49fb7acb301fcf26f80fe9190688(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_6e768ecbca6e75bbe2c933dabcadaee2
    def get_inputs(self):
        return [
            paddle.uniform([1, 480, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4cdd16c01bd63b0b75610cf0280e129f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c5ada77aea41c1b14fb8d9e874274ab8
    def get_inputs(self):
        return [
            paddle.uniform([1, 672, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4ea1b1f9f24b2cd69b4b3f5ae2922ddc(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_87526143ba591b5e347947beca130c76
    def get_inputs(self):
        return [
            paddle.uniform([1, 72, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_d83fa2beee3b09bea615452645e40331(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 576, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_1e80fa63a9186d94ea3141c9655c5d84(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_d83fa2beee3b09bea615452645e40331
    def get_inputs(self):
        return [
            paddle.uniform([1, 576, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_173a788c7dcc2e2fae557fbff395174a(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_64b3612fb370de353a1b268c3b821236
    def get_inputs(self):
        return [
            paddle.uniform([1, 768, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_58fad75e452dee2cc5c594046d460648(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_84793998d56a5b43308d58069fd7187d
    def get_inputs(self):
        return [
            paddle.uniform([1, 576, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_1e80fa63a9186d94ea3141c9655c5d84(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_d83fa2beee3b09bea615452645e40331
    def get_inputs(self):
        return [
            paddle.uniform([1, 576, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_76186274a8f7c7d0e7d5c3152ccec758(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ac586694e388164438a8f3fe885eece7
    def get_inputs(self):
        return [
            paddle.uniform([1, 384, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4cdd16c01bd63b0b75610cf0280e129f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c5ada77aea41c1b14fb8d9e874274ab8
    def get_inputs(self):
        return [
            paddle.uniform([1, 672, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_6d034535ffb2022244834dfbb95b59ad(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e8e48567d534d700c51eb2a8fb93f95d
    def get_inputs(self):
        return [
            paddle.uniform([1, 240, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_d67683acc6e169e88087ec5fa7b63001(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e6a06100d93af8c10246d4d9b29f0be6
    def get_inputs(self):
        return [
            paddle.uniform([1, 72, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_bc505fdcaf85a2fe10f0aa1f464cf90e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c177c5e1c474f3174532ce773e1de32
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4ea1b1f9f24b2cd69b4b3f5ae2922ddc(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_87526143ba591b5e347947beca130c76
    def get_inputs(self):
        return [
            paddle.uniform([1, 72, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_21f695c7bac04e3be9dcf20b1bbb6af3(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_331e94bee2bd309814f937015f72199a
    def get_inputs(self):
        return [
            paddle.uniform([1, 48, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_bc505fdcaf85a2fe10f0aa1f464cf90e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c177c5e1c474f3174532ce773e1de32
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_9f00f04fb884c3d958e4e70992be8bfb(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e2a1c1a79597dfe808eaa0d0049ddaa9
    def get_inputs(self):
        return [
            paddle.uniform([1, 192, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_d67683acc6e169e88087ec5fa7b63001(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e6a06100d93af8c10246d4d9b29f0be6
    def get_inputs(self):
        return [
            paddle.uniform([1, 72, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_daa3c17d2bdad7e3ef413762a3195594(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e181865e0ba9f8a0e82bd65bd8272122
    def get_inputs(self):
        return [
            paddle.uniform([1, 120, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_9f00f04fb884c3d958e4e70992be8bfb(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e2a1c1a79597dfe808eaa0d0049ddaa9
    def get_inputs(self):
        return [
            paddle.uniform([1, 192, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_9f00f04fb884c3d958e4e70992be8bfb(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e2a1c1a79597dfe808eaa0d0049ddaa9
    def get_inputs(self):
        return [
            paddle.uniform([1, 192, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_3244ea5ab118ad2b2c431328f2879520(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_0b02b820ca3845b450ccc06fc185d037
    def get_inputs(self):
        return [
            paddle.uniform([1, 128, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_596ffab083ab7f492fd2c4eb0df867f1(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 144, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_fe75e5bdc21000adfeda2add9b20bd24(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_596ffab083ab7f492fd2c4eb0df867f1
    def get_inputs(self):
        return [
            paddle.uniform([1, 144, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_bc505fdcaf85a2fe10f0aa1f464cf90e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c177c5e1c474f3174532ce773e1de32
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_76186274a8f7c7d0e7d5c3152ccec758(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ac586694e388164438a8f3fe885eece7
    def get_inputs(self):
        return [
            paddle.uniform([1, 384, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_173a788c7dcc2e2fae557fbff395174a(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_64b3612fb370de353a1b268c3b821236
    def get_inputs(self):
        return [
            paddle.uniform([1, 768, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4cdd16c01bd63b0b75610cf0280e129f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c5ada77aea41c1b14fb8d9e874274ab8
    def get_inputs(self):
        return [
            paddle.uniform([1, 672, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_eb3a6d793e39f6ca50f69b7a3168f3c2(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 288, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_c35f382873cfe2a3f3972e4c53784028(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_eb3a6d793e39f6ca50f69b7a3168f3c2
    def get_inputs(self):
        return [
            paddle.uniform([1, 288, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_21f695c7bac04e3be9dcf20b1bbb6af3(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_331e94bee2bd309814f937015f72199a
    def get_inputs(self):
        return [
            paddle.uniform([1, 48, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_76186274a8f7c7d0e7d5c3152ccec758(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ac586694e388164438a8f3fe885eece7
    def get_inputs(self):
        return [
            paddle.uniform([1, 384, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_d67683acc6e169e88087ec5fa7b63001(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e6a06100d93af8c10246d4d9b29f0be6
    def get_inputs(self):
        return [
            paddle.uniform([1, 72, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_8c094cc016ba7897b5967af20d17d184(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.2, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 240, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_4e81667b41779817dc3a50028e5c1305(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c094cc016ba7897b5967af20d17d184
    def get_inputs(self):
        return [
            paddle.uniform([1, 240, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_c17a3f4a55ad6e95a6f4ee66e017e71d(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_5e2ab8415cdd5e6e19c4c55b98d4b1b7
    def get_inputs(self):
        return [
            paddle.uniform([1, 160, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_bc505fdcaf85a2fe10f0aa1f464cf90e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c177c5e1c474f3174532ce773e1de32
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_db942f0524d921fd975140954fa48356(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.2, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 64, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_80de570465d0e79e9092e1c135257cd6(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_db942f0524d921fd975140954fa48356
    def get_inputs(self):
        return [
            paddle.uniform([1, 64, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_92aa49fb7acb301fcf26f80fe9190688(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_6e768ecbca6e75bbe2c933dabcadaee2
    def get_inputs(self):
        return [
            paddle.uniform([1, 480, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_d67683acc6e169e88087ec5fa7b63001(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e6a06100d93af8c10246d4d9b29f0be6
    def get_inputs(self):
        return [
            paddle.uniform([1, 72, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_21f695c7bac04e3be9dcf20b1bbb6af3(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_331e94bee2bd309814f937015f72199a
    def get_inputs(self):
        return [
            paddle.uniform([1, 48, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_bc505fdcaf85a2fe10f0aa1f464cf90e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c177c5e1c474f3174532ce773e1de32
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_f2422b49a901c575187161687a043710(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_6e935281a74f84740567baf06dd39234
    def get_inputs(self):
        return [
            paddle.to_tensor([[[[1.6769212484359741]], [[0.6443898677825928]], [[1.6833102703094482]], [[1.8416796922683716]], [[1.7907239198684692]], [[1.7854830026626587]], [[2.1418089866638184]], [[1.9228086471557617]], [[1.9239948987960815]], [[0.9210250377655029]], [[1.8123711347579956]], [[2.5754528045654297]], [[1.5861111879348755]], [[1.3102155923843384]], [[1.9500722885131836]], [[0.4396582245826721]]]], dtype='float32').reshape([1, 16, 1, 1]),
        ]


class TestPrimitiveOp_9f00f04fb884c3d958e4e70992be8bfb(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e2a1c1a79597dfe808eaa0d0049ddaa9
    def get_inputs(self):
        return [
            paddle.uniform([1, 192, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4e81667b41779817dc3a50028e5c1305(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c094cc016ba7897b5967af20d17d184
    def get_inputs(self):
        return [
            paddle.uniform([1, 240, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_873fef0881c4350ef309136433df873a(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ec9d38a776abf5ba1e4f243247f6880a
    def get_inputs(self):
        return [
            paddle.uniform([1, 256, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_f082828ca2b281c978c788786e552aa1(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 400, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_a30c450c584c408def3e4b2c5f83a96e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_f082828ca2b281c978c788786e552aa1
    def get_inputs(self):
        return [
            paddle.uniform([1, 400, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_6d034535ffb2022244834dfbb95b59ad(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e8e48567d534d700c51eb2a8fb93f95d
    def get_inputs(self):
        return [
            paddle.uniform([1, 240, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_343b9d8f8f263e262c01416b8dcb65d0(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 960, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_f45e6621b7efca7b8f71347617003f43(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_343b9d8f8f263e262c01416b8dcb65d0
    def get_inputs(self):
        return [
            paddle.uniform([1, 960, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_29eea5cc5f8ac1441add15c9ae7c042f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_f79edaa32ac6c3071c3fd00dce083d79
    def get_inputs(self):
        return [
            paddle.uniform([1, 480, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_9f00f04fb884c3d958e4e70992be8bfb(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e2a1c1a79597dfe808eaa0d0049ddaa9
    def get_inputs(self):
        return [
            paddle.uniform([1, 192, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4cdd16c01bd63b0b75610cf0280e129f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c5ada77aea41c1b14fb8d9e874274ab8
    def get_inputs(self):
        return [
            paddle.uniform([1, 672, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_c2b45a2bfdae3d6d6790aafbac992415(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_1ca16c2429fb25bce935f97b484db58f
    def get_inputs(self):
        return [
            paddle.uniform([1, 80, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_b44e725aa1d8afd6dc78b773b81b5a2f(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.2, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 336, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_01cf25ad4f7d286bcfc2715bc243adee(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_b44e725aa1d8afd6dc78b773b81b5a2f
    def get_inputs(self):
        return [
            paddle.uniform([1, 336, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_bc505fdcaf85a2fe10f0aa1f464cf90e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c177c5e1c474f3174532ce773e1de32
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_21f695c7bac04e3be9dcf20b1bbb6af3(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_331e94bee2bd309814f937015f72199a
    def get_inputs(self):
        return [
            paddle.uniform([1, 48, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_c2b45a2bfdae3d6d6790aafbac992415(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_1ca16c2429fb25bce935f97b484db58f
    def get_inputs(self):
        return [
            paddle.uniform([1, 80, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_18e88055cf1f13d94f9bb7715e16ac44(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_6c53ad76abc8e8d50f55fee93f7fb47c
    def get_inputs(self):
        return [
            paddle.uniform([1, 44, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_92aa49fb7acb301fcf26f80fe9190688(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_6e768ecbca6e75bbe2c933dabcadaee2
    def get_inputs(self):
        return [
            paddle.uniform([1, 480, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_a30c450c584c408def3e4b2c5f83a96e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_f082828ca2b281c978c788786e552aa1
    def get_inputs(self):
        return [
            paddle.uniform([1, 400, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_e610a5e2542707be4f4a088019ddc6a7(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 56, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_e1482c60edc833e84d5217b2c1d69c63(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e610a5e2542707be4f4a088019ddc6a7
    def get_inputs(self):
        return [
            paddle.uniform([1, 56, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_76186274a8f7c7d0e7d5c3152ccec758(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ac586694e388164438a8f3fe885eece7
    def get_inputs(self):
        return [
            paddle.uniform([1, 384, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_29eea5cc5f8ac1441add15c9ae7c042f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_f79edaa32ac6c3071c3fd00dce083d79
    def get_inputs(self):
        return [
            paddle.uniform([1, 480, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_fe75e5bdc21000adfeda2add9b20bd24(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_596ffab083ab7f492fd2c4eb0df867f1
    def get_inputs(self):
        return [
            paddle.uniform([1, 144, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_c17a3f4a55ad6e95a6f4ee66e017e71d(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_5e2ab8415cdd5e6e19c4c55b98d4b1b7
    def get_inputs(self):
        return [
            paddle.uniform([1, 160, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_c2b45a2bfdae3d6d6790aafbac992415(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_1ca16c2429fb25bce935f97b484db58f
    def get_inputs(self):
        return [
            paddle.uniform([1, 80, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_76186274a8f7c7d0e7d5c3152ccec758(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ac586694e388164438a8f3fe885eece7
    def get_inputs(self):
        return [
            paddle.uniform([1, 384, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_85630df1db5f563fe79fea251a2c71c2(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.2, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[2, 96, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_64620bb4de26d39cab33f7ab9d4a506a(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_85630df1db5f563fe79fea251a2c71c2
    def get_inputs(self):
        return [
            paddle.uniform([2, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_64620bb4de26d39cab33f7ab9d4a506a(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_85630df1db5f563fe79fea251a2c71c2
    def get_inputs(self):
        return [
            paddle.uniform([2, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_64620bb4de26d39cab33f7ab9d4a506a(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_85630df1db5f563fe79fea251a2c71c2
    def get_inputs(self):
        return [
            paddle.uniform([2, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_64620bb4de26d39cab33f7ab9d4a506a(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_85630df1db5f563fe79fea251a2c71c2
    def get_inputs(self):
        return [
            paddle.uniform([2, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_4cf780d550f2b797fc579673ce038090(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.2, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[2, 24, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_4095d1f0375a3b22d0609958e35b936a(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_4cf780d550f2b797fc579673ce038090
    def get_inputs(self):
        return [
            paddle.uniform([2, 24, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4095d1f0375a3b22d0609958e35b936a(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_4cf780d550f2b797fc579673ce038090
    def get_inputs(self):
        return [
            paddle.uniform([2, 24, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4095d1f0375a3b22d0609958e35b936a(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_4cf780d550f2b797fc579673ce038090
    def get_inputs(self):
        return [
            paddle.uniform([2, 24, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4095d1f0375a3b22d0609958e35b936a(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_4cf780d550f2b797fc579673ce038090
    def get_inputs(self):
        return [
            paddle.uniform([2, 24, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_92aa49fb7acb301fcf26f80fe9190688(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_6e768ecbca6e75bbe2c933dabcadaee2
    def get_inputs(self):
        return [
            paddle.uniform([1, 480, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_9f00f04fb884c3d958e4e70992be8bfb(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e2a1c1a79597dfe808eaa0d0049ddaa9
    def get_inputs(self):
        return [
            paddle.uniform([1, 192, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_f9f0092946410c5b46b82831d1f41c74(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_0d01762121dbb8c04d505ae04a4ae0a3
    def get_inputs(self):
        return [
            paddle.uniform([1, 120, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_f9f0092946410c5b46b82831d1f41c74(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_0d01762121dbb8c04d505ae04a4ae0a3
    def get_inputs(self):
        return [
            paddle.uniform([1, 120, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_f9f0092946410c5b46b82831d1f41c74(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_0d01762121dbb8c04d505ae04a4ae0a3
    def get_inputs(self):
        return [
            paddle.uniform([1, 120, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_8d772694a0bca7288e934d5eaac3ab88(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.166667, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 200, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_273d02485caea706e14842369b9a9ecd(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8d772694a0bca7288e934d5eaac3ab88
    def get_inputs(self):
        return [
            paddle.uniform([1, 200, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4e81667b41779817dc3a50028e5c1305(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c094cc016ba7897b5967af20d17d184
    def get_inputs(self):
        return [
            paddle.uniform([1, 240, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_76186274a8f7c7d0e7d5c3152ccec758(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ac586694e388164438a8f3fe885eece7
    def get_inputs(self):
        return [
            paddle.uniform([1, 384, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_f9f0092946410c5b46b82831d1f41c74(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_0d01762121dbb8c04d505ae04a4ae0a3
    def get_inputs(self):
        return [
            paddle.uniform([1, 120, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_21f695c7bac04e3be9dcf20b1bbb6af3(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_331e94bee2bd309814f937015f72199a
    def get_inputs(self):
        return [
            paddle.uniform([1, 48, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_21f695c7bac04e3be9dcf20b1bbb6af3(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_331e94bee2bd309814f937015f72199a
    def get_inputs(self):
        return [
            paddle.uniform([1, 48, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_8a1e5809c8e2ff4f705bc947bd646a11(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ef4004d2bfd110446d0cd9fc2342a3ba
    def get_inputs(self):
        return [
            paddle.uniform([1, 100, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_6d034535ffb2022244834dfbb95b59ad(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e8e48567d534d700c51eb2a8fb93f95d
    def get_inputs(self):
        return [
            paddle.uniform([1, 240, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_b25eb871be0a67ba974dde73fe3d430f(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.2, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 288, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_7ac894f047d9b160d6a876a60b30ff0d(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_b25eb871be0a67ba974dde73fe3d430f
    def get_inputs(self):
        return [
            paddle.uniform([1, 288, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_76186274a8f7c7d0e7d5c3152ccec758(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ac586694e388164438a8f3fe885eece7
    def get_inputs(self):
        return [
            paddle.uniform([1, 384, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_173a788c7dcc2e2fae557fbff395174a(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_64b3612fb370de353a1b268c3b821236
    def get_inputs(self):
        return [
            paddle.uniform([1, 768, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_c35f382873cfe2a3f3972e4c53784028(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_eb3a6d793e39f6ca50f69b7a3168f3c2
    def get_inputs(self):
        return [
            paddle.uniform([1, 288, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_21f695c7bac04e3be9dcf20b1bbb6af3(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_331e94bee2bd309814f937015f72199a
    def get_inputs(self):
        return [
            paddle.uniform([1, 48, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4ea1b1f9f24b2cd69b4b3f5ae2922ddc(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_87526143ba591b5e347947beca130c76
    def get_inputs(self):
        return [
            paddle.uniform([1, 72, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_173a788c7dcc2e2fae557fbff395174a(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_64b3612fb370de353a1b268c3b821236
    def get_inputs(self):
        return [
            paddle.uniform([1, 768, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_9f00f04fb884c3d958e4e70992be8bfb(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e2a1c1a79597dfe808eaa0d0049ddaa9
    def get_inputs(self):
        return [
            paddle.uniform([1, 192, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_9f00f04fb884c3d958e4e70992be8bfb(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e2a1c1a79597dfe808eaa0d0049ddaa9
    def get_inputs(self):
        return [
            paddle.uniform([1, 192, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_9f00f04fb884c3d958e4e70992be8bfb(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e2a1c1a79597dfe808eaa0d0049ddaa9
    def get_inputs(self):
        return [
            paddle.uniform([1, 192, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_273d02485caea706e14842369b9a9ecd(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8d772694a0bca7288e934d5eaac3ab88
    def get_inputs(self):
        return [
            paddle.uniform([1, 200, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_bc505fdcaf85a2fe10f0aa1f464cf90e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c177c5e1c474f3174532ce773e1de32
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_132a9c56c5542f70b08b59da10d84f9c(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_f13ffc13df02b96e0c965046751b95cf
    def get_inputs(self):
        return [
            paddle.uniform([1, 320, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_bc505fdcaf85a2fe10f0aa1f464cf90e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c177c5e1c474f3174532ce773e1de32
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_92aa49fb7acb301fcf26f80fe9190688(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_6e768ecbca6e75bbe2c933dabcadaee2
    def get_inputs(self):
        return [
            paddle.uniform([1, 480, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_76186274a8f7c7d0e7d5c3152ccec758(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ac586694e388164438a8f3fe885eece7
    def get_inputs(self):
        return [
            paddle.uniform([1, 384, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_bc505fdcaf85a2fe10f0aa1f464cf90e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c177c5e1c474f3174532ce773e1de32
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_a2c7334268a375ef0b05caa831cc17a9(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.2, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 40, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_78a3966e1989ab6b88d70c1396144d89(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_a2c7334268a375ef0b05caa831cc17a9
    def get_inputs(self):
        return [
            paddle.uniform([1, 40, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_76186274a8f7c7d0e7d5c3152ccec758(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ac586694e388164438a8f3fe885eece7
    def get_inputs(self):
        return [
            paddle.uniform([1, 384, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_92aa49fb7acb301fcf26f80fe9190688(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_6e768ecbca6e75bbe2c933dabcadaee2
    def get_inputs(self):
        return [
            paddle.uniform([1, 480, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_d67683acc6e169e88087ec5fa7b63001(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e6a06100d93af8c10246d4d9b29f0be6
    def get_inputs(self):
        return [
            paddle.uniform([1, 72, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_c35f382873cfe2a3f3972e4c53784028(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_eb3a6d793e39f6ca50f69b7a3168f3c2
    def get_inputs(self):
        return [
            paddle.uniform([1, 288, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4cdd16c01bd63b0b75610cf0280e129f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c5ada77aea41c1b14fb8d9e874274ab8
    def get_inputs(self):
        return [
            paddle.uniform([1, 672, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4cdd16c01bd63b0b75610cf0280e129f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c5ada77aea41c1b14fb8d9e874274ab8
    def get_inputs(self):
        return [
            paddle.uniform([1, 672, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_6d034535ffb2022244834dfbb95b59ad(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e8e48567d534d700c51eb2a8fb93f95d
    def get_inputs(self):
        return [
            paddle.uniform([1, 240, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_f9f0092946410c5b46b82831d1f41c74(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_0d01762121dbb8c04d505ae04a4ae0a3
    def get_inputs(self):
        return [
            paddle.uniform([1, 120, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_c17a3f4a55ad6e95a6f4ee66e017e71d(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_5e2ab8415cdd5e6e19c4c55b98d4b1b7
    def get_inputs(self):
        return [
            paddle.uniform([1, 160, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_21f695c7bac04e3be9dcf20b1bbb6af3(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_331e94bee2bd309814f937015f72199a
    def get_inputs(self):
        return [
            paddle.uniform([1, 48, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_ab77adfa52800ffaedacc5af48e4900f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e98a6057ab8ac29e7554ebf80879f084
    def get_inputs(self):
        return [
            paddle.uniform([1, 64, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_3244ea5ab118ad2b2c431328f2879520(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_0b02b820ca3845b450ccc06fc185d037
    def get_inputs(self):
        return [
            paddle.uniform([1, 128, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_b456627706ce1b62e77a420ec9ad3c45(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.2, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 144, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_d4291af32fe3e07695d71e77b7ce91e5(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_b456627706ce1b62e77a420ec9ad3c45
    def get_inputs(self):
        return [
            paddle.uniform([1, 144, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_01cf25ad4f7d286bcfc2715bc243adee(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_b44e725aa1d8afd6dc78b773b81b5a2f
    def get_inputs(self):
        return [
            paddle.uniform([1, 336, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_fe75e5bdc21000adfeda2add9b20bd24(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_596ffab083ab7f492fd2c4eb0df867f1
    def get_inputs(self):
        return [
            paddle.uniform([1, 144, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_76186274a8f7c7d0e7d5c3152ccec758(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ac586694e388164438a8f3fe885eece7
    def get_inputs(self):
        return [
            paddle.uniform([1, 384, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_e1482c60edc833e84d5217b2c1d69c63(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e610a5e2542707be4f4a088019ddc6a7
    def get_inputs(self):
        return [
            paddle.uniform([1, 56, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_1e80fa63a9186d94ea3141c9655c5d84(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_d83fa2beee3b09bea615452645e40331
    def get_inputs(self):
        return [
            paddle.uniform([1, 576, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_c2b45a2bfdae3d6d6790aafbac992415(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_1ca16c2429fb25bce935f97b484db58f
    def get_inputs(self):
        return [
            paddle.uniform([1, 80, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_132a9c56c5542f70b08b59da10d84f9c(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_f13ffc13df02b96e0c965046751b95cf
    def get_inputs(self):
        return [
            paddle.uniform([1, 320, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_f9f0092946410c5b46b82831d1f41c74(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_0d01762121dbb8c04d505ae04a4ae0a3
    def get_inputs(self):
        return [
            paddle.uniform([1, 120, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_de1046a18a5f5319903d1e2b075a1ee2(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_74a9c3274e82fd70e05b97a97c64f676
    def get_inputs(self):
        return [
            paddle.uniform([1, 960, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_9f00f04fb884c3d958e4e70992be8bfb(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e2a1c1a79597dfe808eaa0d0049ddaa9
    def get_inputs(self):
        return [
            paddle.uniform([1, 192, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_c17a3f4a55ad6e95a6f4ee66e017e71d(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_5e2ab8415cdd5e6e19c4c55b98d4b1b7
    def get_inputs(self):
        return [
            paddle.uniform([1, 160, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_d4291af32fe3e07695d71e77b7ce91e5(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_b456627706ce1b62e77a420ec9ad3c45
    def get_inputs(self):
        return [
            paddle.uniform([1, 144, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4ea1b1f9f24b2cd69b4b3f5ae2922ddc(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_87526143ba591b5e347947beca130c76
    def get_inputs(self):
        return [
            paddle.uniform([1, 72, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_f45e6621b7efca7b8f71347617003f43(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_343b9d8f8f263e262c01416b8dcb65d0
    def get_inputs(self):
        return [
            paddle.uniform([1, 960, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_9f00f04fb884c3d958e4e70992be8bfb(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e2a1c1a79597dfe808eaa0d0049ddaa9
    def get_inputs(self):
        return [
            paddle.uniform([1, 192, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_daa3c17d2bdad7e3ef413762a3195594(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_e181865e0ba9f8a0e82bd65bd8272122
    def get_inputs(self):
        return [
            paddle.uniform([1, 120, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_273d02485caea706e14842369b9a9ecd(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8d772694a0bca7288e934d5eaac3ab88
    def get_inputs(self):
        return [
            paddle.uniform([1, 200, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_a30c450c584c408def3e4b2c5f83a96e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_f082828ca2b281c978c788786e552aa1
    def get_inputs(self):
        return [
            paddle.uniform([1, 400, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_bc505fdcaf85a2fe10f0aa1f464cf90e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c177c5e1c474f3174532ce773e1de32
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_bc505fdcaf85a2fe10f0aa1f464cf90e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c177c5e1c474f3174532ce773e1de32
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_8a1e5809c8e2ff4f705bc947bd646a11(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_ef4004d2bfd110446d0cd9fc2342a3ba
    def get_inputs(self):
        return [
            paddle.uniform([1, 100, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_21f695c7bac04e3be9dcf20b1bbb6af3(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_331e94bee2bd309814f937015f72199a
    def get_inputs(self):
        return [
            paddle.uniform([1, 48, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_92aa49fb7acb301fcf26f80fe9190688(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_6e768ecbca6e75bbe2c933dabcadaee2
    def get_inputs(self):
        return [
            paddle.uniform([1, 480, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_c17a3f4a55ad6e95a6f4ee66e017e71d(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_5e2ab8415cdd5e6e19c4c55b98d4b1b7
    def get_inputs(self):
        return [
            paddle.uniform([1, 160, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_132a9c56c5542f70b08b59da10d84f9c(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_f13ffc13df02b96e0c965046751b95cf
    def get_inputs(self):
        return [
            paddle.uniform([1, 320, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_3244ea5ab118ad2b2c431328f2879520(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_0b02b820ca3845b450ccc06fc185d037
    def get_inputs(self):
        return [
            paddle.uniform([1, 128, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_c17a3f4a55ad6e95a6f4ee66e017e71d(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_5e2ab8415cdd5e6e19c4c55b98d4b1b7
    def get_inputs(self):
        return [
            paddle.uniform([1, 160, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_92aa49fb7acb301fcf26f80fe9190688(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_6e768ecbca6e75bbe2c933dabcadaee2
    def get_inputs(self):
        return [
            paddle.uniform([1, 480, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_bc505fdcaf85a2fe10f0aa1f464cf90e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8c177c5e1c474f3174532ce773e1de32
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_6c710e32bdedbea78331a048c69e2c54(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c2ffdc91577917ee4518ce373991df84
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_6c710e32bdedbea78331a048c69e2c54(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c2ffdc91577917ee4518ce373991df84
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_6c710e32bdedbea78331a048c69e2c54(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c2ffdc91577917ee4518ce373991df84
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_6c710e32bdedbea78331a048c69e2c54(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c2ffdc91577917ee4518ce373991df84
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class PrimitiveOp_cf8dfebaba8dae40958068dc41fcad73(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0):
        return paddle._C_ops.hardsigmoid(input_0, 0.2, 0.5)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1, 24, 1, 1], dtype='float32'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_da36871176f5f50494490cc219d4362d(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_cf8dfebaba8dae40958068dc41fcad73
    def get_inputs(self):
        return [
            paddle.to_tensor([[[[56648.40234375]], [[64627.09765625]], [[68931.9140625]], [[47124.8984375]], [[72621.3671875]], [[35393.01171875]], [[50048.0859375]], [[59094.8359375]], [[42497.83984375]], [[59709.453125]], [[49656.55078125]], [[52544.984375]], [[12997.0283203125]], [[26224.818359375]], [[43233.953125]], [[48868.90234375]], [[41799.6484375]], [[35428.05859375]], [[44814.65625]], [[43367.41796875]], [[51649.94140625]], [[39551.62890625]], [[61464.578125]], [[39888.69921875]]]], dtype='float32').reshape([1, 24, 1, 1]),
        ]


class TestPrimitiveOp_1accb3f2f559d21d4df270960babc512(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_cf8dfebaba8dae40958068dc41fcad73
    def get_inputs(self):
        return [
            paddle.to_tensor([[[[87636.078125]], [[65017.7890625]], [[63726.93359375]], [[91773.3203125]], [[45724.90625]], [[97858.03125]], [[42543.0703125]], [[62596.328125]], [[57506.390625]], [[60892.03125]], [[49574.48828125]], [[38106.51953125]], [[61890.37109375]], [[58755.90234375]], [[61959.45703125]], [[93317.53125]], [[86211.4609375]], [[42468.9921875]], [[55115.578125]], [[37926.6796875]], [[55694.91796875]], [[83752.890625]], [[63526.3984375]], [[58625.8671875]]]], dtype='float32').reshape([1, 24, 1, 1]),
        ]


class TestPrimitiveOp_1edfb6662fbcc4871aec419f741f4b37(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_cf8dfebaba8dae40958068dc41fcad73
    def get_inputs(self):
        return [
            paddle.to_tensor([[[[68718.796875]], [[64992.94140625]], [[69150.9921875]], [[43207.16015625]], [[63480.25390625]], [[58335.3203125]], [[80166.3359375]], [[62509.84765625]], [[63098.17578125]], [[48263.453125]], [[34410.87109375]], [[46860.65625]], [[63439.89453125]], [[54862.98046875]], [[68767.2421875]], [[52991.85546875]], [[38973.37890625]], [[67475.3828125]], [[44318.12109375]], [[65171.1171875]], [[71244.6875]], [[63659.36328125]], [[65752.59375]], [[51634.7734375]]]], dtype='float32').reshape([1, 24, 1, 1]),
        ]


class TestPrimitiveOp_7ab366d103f4d256ccd447ac22fa0f0e(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_cf8dfebaba8dae40958068dc41fcad73
    def get_inputs(self):
        return [
            paddle.to_tensor([[[[65182.65234375]], [[64773.07421875]], [[85188.1953125]], [[71612.171875]], [[70390.125]], [[66592.7109375]], [[100533.15625]], [[81087.75]], [[66857.4765625]], [[61894.734375]], [[47631.87890625]], [[76956.5078125]], [[77162.953125]], [[34406.8359375]], [[74844.1328125]], [[73234.3984375]], [[72689.5546875]], [[67419.2109375]], [[61779.41796875]], [[49913.65625]], [[47483.62890625]], [[101989.1328125]], [[87359.96875]], [[41021.37890625]]]], dtype='float32').reshape([1, 24, 1, 1]),
        ]


class TestPrimitiveOp_de1046a18a5f5319903d1e2b075a1ee2(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_74a9c3274e82fd70e05b97a97c64f676
    def get_inputs(self):
        return [
            paddle.uniform([1, 960, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_7ac894f047d9b160d6a876a60b30ff0d(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_b25eb871be0a67ba974dde73fe3d430f
    def get_inputs(self):
        return [
            paddle.uniform([1, 288, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_6c710e32bdedbea78331a048c69e2c54(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c2ffdc91577917ee4518ce373991df84
    def get_inputs(self):
        return [
            paddle.uniform([1, 96, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4ea1b1f9f24b2cd69b4b3f5ae2922ddc(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_87526143ba591b5e347947beca130c76
    def get_inputs(self):
        return [
            paddle.uniform([1, 72, 1, 1], dtype='float32', min=0, max=0.5),
        ]


class TestPrimitiveOp_4cdd16c01bd63b0b75610cf0280e129f(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_c5ada77aea41c1b14fb8d9e874274ab8
    def get_inputs(self):
        return [
            paddle.uniform([1, 672, 1, 1], dtype='float32', min=0, max=0.5),
        ]




if __name__ == '__main__':
    unittest.main()
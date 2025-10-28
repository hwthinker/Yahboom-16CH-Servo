#include "ti_msp_dl_config.h"
#include "delay.h"
#include "bsp_i2c_gpio.h"

int main(void)
{
	int  i=0;
    SYSCFG_DL_init();
			
    while (1)
    {
		for(i = 0;i<180;i+=5){
			IIC_Servo(1,i);
		}
		IIC_Servo(1,0);
    }
}

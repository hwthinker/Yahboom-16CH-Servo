#include "ti_msp_dl_config.h"
#include "delay.h"
#include "usart.h"


int main(void)
{
	int  i=0;
    USART_Init();
	
    while (1)
    {
		for(i = 0;i<180;i+=5){
			UART_Servo(1,i);
		}
		UART_Servo(1,0);
    }
}

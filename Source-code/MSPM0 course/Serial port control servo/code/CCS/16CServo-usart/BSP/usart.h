#ifndef	__USART_H__
#define __USART_H__

#include "ti_msp_dl_config.h"

void USART_Init(void);

static void USART_SendData(unsigned char data);
void UART_Servo(unsigned char servonum,unsigned char angle);



#endif

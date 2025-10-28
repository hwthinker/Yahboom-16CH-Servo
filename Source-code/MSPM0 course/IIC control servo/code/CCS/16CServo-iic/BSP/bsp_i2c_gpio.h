#ifndef _BSP_I2C_GPIO_H
#define _BSP_I2C_GPIO_H


#include <inttypes.h>



#define I2C_ADDR                    0x5A   

#define macI2C_WR	0		/* д����bit	Write control bit */
#define macI2C_RD	1		/* ������bit	Read control bit */


/* ����I2C�������ӵ�GPIO�˿�, �û�ֻ��Ҫ�޸�����4�д��뼴������ı�SCL��SDA������ */
/* Define the GPIO port connected to the I2C bus. Users only need to modify the following 4 lines of code to change the SCL and SDA pins at will */
#define macGPIO_PORT_I2C	GPIOB			/* GPIO�˿� GPIO Ports*/
#define macRCC_I2C_PORT 	RCC_APB2Periph_GPIOB		/* GPIO�˿�ʱ�� GPIO port clock*/
#define macI2C_SCL_PIN		SCL_PIN_6_PIN			/* ���ӵ�SCLʱ���ߵ�GPIO GPIO connected to SCL clock line*/
#define macI2C_SDA_PIN		SDA_PIN_7_PIN			/* ���ӵ�SDA�����ߵ�GPIO GPIO connected to SDA data line*/


#define macI2C_SCL_1()  DL_GPIO_setPins(macGPIO_PORT_I2C, macI2C_SCL_PIN)		/* SCL = 1 */
#define macI2C_SCL_0()  DL_GPIO_clearPins(macGPIO_PORT_I2C, macI2C_SCL_PIN)		/* SCL = 0 */

#define macI2C_SDA_1()  DL_GPIO_setPins(macGPIO_PORT_I2C, macI2C_SDA_PIN)		/* SDA = 1 */
#define macI2C_SDA_0()  DL_GPIO_clearPins(macGPIO_PORT_I2C, macI2C_SDA_PIN)		/* SDA = 0 */

#define macI2C_SDA_READ()  DL_GPIO_readPins(macGPIO_PORT_I2C, macI2C_SDA_PIN)	/* ��SDA����״̬ Read SDA line status*/
#define macI2C_SCL_READ()  DL_GPIO_readPins(macGPIO_PORT_I2C, macI2C_SCL_PIN)	/* ��SCL����״̬ Read SCL line status*/


void Start_I2c(void);
void Stop_I2c(void);
void  I2C_SendByte(unsigned char  c);
unsigned char I2C_RcvByte(void);
void Ack_I2c(uint8_t a);

uint8_t IIC_Servo(unsigned char servonum,unsigned char angle);

void delay(int z);

#endif


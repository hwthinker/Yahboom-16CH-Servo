#include "bsp_i2c_gpio.h"
#include "ti_msp_dl_config.h"
#include <string.h>
#include "delay.h"

uint8_t ack;                 /*应答标志位*//*Response sign*/
/*
*********************************************************************************************************
*	函 数 名: i2c_Delay                     Function name: I2C_Dlay
*	功能说明: I2C总线位延迟，最快400KHz      Function description: I2C bus position delay, fastest 400kHz
*	形    参：无                           Shape: None
*	返 回 值: 无                           Return value: none
*********************************************************************************************************
*/

static void i2c_Delay(void)
{
	delay_us(100);
}


void delay(int z)
{   
	  int i;
	  int j;
	  for(i = 0;i<z;i++)
		{
			for(j = 0;j<50;j++)
			{
					i2c_Delay();
				}
		}
}

/*
*********************************************************************************************************
*	函 数 名: i2c_Start                 * Function name: I2C_START
*	功能说明: CPU发起I2C总线启动信号     * Function description: CPU launches I2C bus start signal 
*	形    参：无                         * Shape: None
*	返 回 值: 无                         * Return value: none
*********************************************************************************************************
*/

void Start_I2c(void)
{
  macI2C_SDA_1();         /*发送起始条件的数据信号  Data signals of sending starting conditions*/
  macI2C_SCL_1();
  i2c_Delay();    
  macI2C_SDA_0();
  i2c_Delay();       
  macI2C_SCL_0();       /*钳住I2C总线，准备发送或接收数据   Clamp the I2C bus and prepare to send or receive data*/
  i2c_Delay();
}
/*
*********************************************************************************************************
*	函 数 名: i2c_Stop                  * Function name: I2C_STOP
*	功能说明: CPU发起I2C总线停止信号     * Function description: CPU initiates I2C bus stop signal
*	形    参：无                       * Shape: None
*	返 回 值: 无                       * Return value: none
*********************************************************************************************************
*/
void Stop_I2c(void)
{
	/* 当SCL高电平时，SDA出现一个上跳沿表示I2C总线停止信号 When SCL is high, an upper binding of the SDA indicates that the I2C bus stop signal*/
	macI2C_SDA_0();
	macI2C_SCL_1();
	i2c_Delay();
	macI2C_SDA_1();
	i2c_Delay();
}

/*
*********************************************************************************************************
*	函 数 名: i2c_SendByte                     * Sweeping name: I2C_SENDBYTE
*	功能说明: CPU向I2C总线设备发送8bit数据       * Function description: CPU sends 8bit data to the I2C bus device
*	形    参：_ucByte ： 等待发送的字节         * Icing: _UCBYTE: The bytes waiting to be sent
*	返 回 值: 无                               * Return value: none
*********************************************************************************************************
*/

void  I2C_SendByte(unsigned char  c)
{
 unsigned char  i;
 
 for(i=0;i<8;i++)  /*要传送的数据长度为8位  The length of the data to be transmitted is 8 bits*/
    {
     if((c<<i)&0x80) macI2C_SDA_1();   /*判断发送位  Judgment sending bit*/
       else  macI2C_SDA_0();                
     i2c_Delay();
     macI2C_SCL_1();               /*置时钟线为高，通知被控器开始接收数据位  The clock line is high, notify the controller to start receiving the data bit*/
      i2c_Delay();
			
     macI2C_SCL_0();
    }
    i2c_Delay();
    macI2C_SDA_1() ;                /*8位发送完后释放数据线，准备接收应答位 Release the data cable after the 8 -bit is sent, and prepare to receive the answer*/
    i2c_Delay();   
    macI2C_SCL_1();
    i2c_Delay();
    if(macI2C_SDA_READ())ack=0;     
       else ack=1;        /*判断是否接收到应答信号  Determine whether to receive the answer signal*/
    macI2C_SCL_0();
    i2c_Delay();

}

/*
*********************************************************************************************************
*	函 数 名: i2c_ReadByte                     * Function name: I2C_READBYTE
*	功能说明: CPU从I2C总线设备读取8bit数据      * Function description: CPU reads 8bit data from the I2C bus device
*	形    参：无                                * Shape: None
*	返 回 值: 读到的数据                        * Return value: read data
*********************************************************************************************************
*/



unsigned char I2C_RcvByte(void)
{
  unsigned char  retc=0,i=0; 
  macI2C_SDA_1();                     /*置数据线为输入方式  The data cable is the input method*/

  for(i=0;i<8;i++)
      {

        i2c_Delay();           
        macI2C_SCL_0();                  /*置时钟线为低，准备接收数据位 The clock line is low, prepare to receive the data bit*/
        i2c_Delay();
        macI2C_SCL_1();                  /*置时钟线为高使数据线上数据有效 The clock line is valid for high -tech data line data*/
        i2c_Delay();
        retc=retc<<1;
        if(macI2C_SDA_READ())retc=retc+1;  /*读数据位,接收的数据位放入retc中 Read the data bit, the receiving data bit is placed in RETC*/
        i2c_Delay();
      } 
  macI2C_SCL_0();    
   i2c_Delay();
  return(retc);
}



/********************************************************************
                     应答子函数     Answer sub -function
********************************************************************/
void Ack_I2c(uint8_t a)
{  
  if(a==0) macI2C_SDA_0();              /*在此发出应答或非应答信号 Send an acknowledgement or non-acknowledgement signal here*/
  else macI2C_SDA_1();				  /*0为发出应答，1为非应答信号 0 is a response, 1 is a non-response signal*/
  i2c_Delay();      
  macI2C_SCL_1();
  i2c_Delay(); 
  macI2C_SCL_0();                    /*清时钟线，住I2C总线以便继续接收  Clear the clock line and hold the I2C bus to continue receiving*/
  i2c_Delay();   
}



uint8_t IIC_Servo(unsigned char servonum,unsigned char angle)
{
  
    Start_I2c();          		//启动总线  Start bus
	I2C_SendByte(I2C_ADDR);     //发送器件地址  Send device address
	if(ack==0)return(0);
   	I2C_SendByte(servonum);    //发送数据 Send data
	if(ack==0)return(0);
   	I2C_SendByte(angle);    //发送数据  Send data
	if(ack==0)return(0);

	Stop_I2c();               //结束总线  End the bus
	delay_ms(100);
   	return(1);

}

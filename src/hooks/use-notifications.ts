import { useState, useEffect, useCallback } from 'react'

export const useNotifications = () => {
  const [permission, setPermission] = useState<NotificationPermission>('default')
  const [isSupported, setIsSupported] = useState(false)

  useEffect(() => {
    console.log('🔔 useNotifications: Verificando suporte...')
    
    const checkSupport = async () => {
      // Verificar se estamos no Electron
      if (window.electronAPI) {
        console.log('🔔 useNotifications: Electron detectado')
        try {
          const supported = await window.electronAPI.isNotificationSupported()
          const perm = await window.electronAPI.getNotificationPermission()
          console.log('🔔 useNotifications: Suporte:', supported, 'Permissão:', perm)
          setIsSupported(supported)
          setPermission(perm)
        } catch (error) {
          console.error('🔔 useNotifications: Erro ao verificar suporte:', error)
          setIsSupported(false)
          setPermission('denied')
        }
      } else {
        console.log('🔔 useNotifications: Navegador detectado')
        // Fallback para navegador
        const supported = 'Notification' in window
        const perm = Notification.permission
        console.log('🔔 useNotifications: Suporte:', supported, 'Permissão:', perm)
        setIsSupported(supported)
        setPermission(perm)
      }
    }
    
    checkSupport()
  }, [])

  const requestPermission = useCallback(async () => {
    if (!isSupported) return false

    try {
      let newPermission: NotificationPermission
      
      if (window.electronAPI) {
        newPermission = await window.electronAPI.requestNotificationPermission()
      } else {
        newPermission = await Notification.requestPermission()
      }
      
      setPermission(newPermission)
      return newPermission === 'granted'
    } catch (error) {
      console.error('Erro ao solicitar permissão de notificação:', error)
      return false
    }
  }, [isSupported])

  const sendNotification = useCallback((title: string, options?: NotificationOptions) => {
    if (permission !== 'granted') return null

    try {
      if (window.electronAPI) {
        return window.electronAPI.sendSystemNotification(title, options)
      } else {
        return new Notification(title, options)
      }
    } catch (error) {
      console.error('Erro ao enviar notificação:', error)
      return null
    }
  }, [permission])

  const notifyFocusLoss = useCallback((level: string) => {
    console.log('🔔 notifyFocusLoss: Chamada com nível:', level, 'Permissão:', permission)
    
    if (permission !== 'granted') {
      console.log('🔔 notifyFocusLoss: Permissão negada, retornando null')
      return null
    }

    try {
      if (window.electronAPI) {
        console.log('🔔 notifyFocusLoss: Usando API do Electron')
        const result = window.electronAPI.notifyFocusLoss(level)
        console.log('🔔 notifyFocusLoss: Resultado Electron:', result)
        return result
      } else {
        console.log('🔔 notifyFocusLoss: Usando API do navegador')
        // Fallback para navegador
        const notification = new Notification('🚨 Perda de Foco Detectada!', {
          body: `Você perdeu o foco na sessão ${level}. Volte para a tela do ClopFocus!`,
          icon: '',
          tag: 'focus-loss',
          requireInteraction: false,
          silent: false
        })
        
        notification.onclick = () => {
          window.focus()
          notification.close()
        }
        
        console.log('🔔 notifyFocusLoss: Notificação do navegador criada:', notification)
        return notification
      }
    } catch (error) {
      console.error('🔔 notifyFocusLoss: Erro:', error)
      return null
    }
  }, [permission])

  return {
    isSupported,
    permission,
    requestPermission,
    sendNotification,
    notifyFocusLoss
  }
}
